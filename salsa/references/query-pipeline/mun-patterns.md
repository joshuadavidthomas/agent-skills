# Mun Query Pipeline Patterns [Legacy API/Architecture]

Mun uses Salsa 2018 (v0.16.1) with `#[salsa::query_group]` macros. All syntax shown here is from the legacy API. Use for **architectural insights** — adapt to modern `#[salsa::tracked]` syntax.

## LLVM Codegen as Salsa Query Endpoint

Mun is the only surveyed project where Salsa's computation graph extends all the way to machine code generation. The `CodeGenDatabase` query group sits atop 5 other layers:

```
SourceDatabase (files, source roots)
  → AstDatabase (parsing)
    → InternDatabase (function/struct/impl IDs)
      → DefDatabase (item trees, package defs, bodies)
        → HirDatabase (type inference, target data layout)
          → CodeGenDatabase (LLVM IR, shared libraries)
```

### The CodeGenDatabase

```rust
// mun_codegen/src/db.rs
#[salsa::query_group(CodeGenDatabaseStorage)]
pub trait CodeGenDatabase: mun_hir::HirDatabase {
    #[salsa::input]
    fn optimization_level(&self) -> inkwell::OptimizationLevel;

    #[salsa::invoke(crate::module_partition::build_partition)]
    fn module_partition(&self) -> Arc<ModulePartition>;

    fn target_machine(&self) -> ByAddress<Rc<inkwell::targets::TargetMachine>>;

    #[salsa::invoke(crate::assembly::build_assembly_ir)]
    fn assembly_ir(&self, module_group: ModuleGroupId) -> Arc<AssemblyIr>;

    #[salsa::invoke(crate::assembly::build_target_assembly)]
    fn target_assembly(&self, module_group: ModuleGroupId) -> Arc<TargetAssembly>;
}
```

The `target_assembly` function is the query endpoint: it creates an LLVM context, builds IR, compiles to an object file, links to a shared library, and returns a `TargetAssembly` pointing to the `.munlib` file on disk. Salsa caches the result — if nothing upstream changed, the shared library isn't rebuilt.

### Non-Send Return Type: `ByAddress<Rc<TargetMachine>>`

LLVM's `TargetMachine` is not `Send` or `Sync`. Mun wraps it in `Rc` (not `Arc`) and uses `ByAddress` for pointer-equality-based caching:

```rust
// mun_codegen/src/db.rs
fn target_machine(db: &dyn CodeGenDatabase) -> ByAddress<Rc<inkwell::targets::TargetMachine>> {
    let target = db.target();
    Target::initialize_x86(&InitializationConfig::default());
    Target::initialize_aarch64(&InitializationConfig::default());

    let target_triple = TargetTriple::create(&db.target().llvm_target);
    let llvm_target = Target::from_triple(&target_triple).expect("...");

    let target_machine = llvm_target.create_target_machine(
        &target_triple,
        &target.options.cpu,
        &target.options.features,
        db.optimization_level(),
        RelocMode::PIC,
        CodeModel::Default,
    ).expect("...");

    ByAddress(Rc::new(target_machine))
}
```

This works because Mun's codegen layer runs single-threaded. The `TargetMachine` is created once per target configuration and cached — it only changes if the target or optimization level changes.

**Key pattern**: When integrating thread-unsafe backends, confine them to a single-threaded layer and use `Rc` + `ByAddress`. The `ByAddress` wrapper provides `Eq`/`Hash` via pointer identity, satisfying Salsa's requirements without requiring the wrapped type to implement those traits.

### Assembly Build Flow

The actual code generation happens in `build_target_assembly`:

```rust
// mun_codegen/src/assembly.rs
pub(crate) fn build_target_assembly(
    db: &dyn CodeGenDatabase,
    module_group: ModuleGroupId,
) -> Arc<TargetAssembly> {
    let inkwell_context = Context::create();
    let code_gen_context = CodeGenContext::new(&inkwell_context, db);

    let assembly = build_assembly(db, &code_gen_context, module_group);
    let obj_file = assembly.into_object_file().expect("...");

    let file = NamedTempFile::new().expect("...");
    obj_file.into_shared_object(file.path()).expect("...");

    Arc::new(TargetAssembly { file })
}
```

The `CodeGenContext` bridges Salsa and LLVM — it holds references to `&dyn HirDatabase` (for type queries) and LLVM objects:

```rust
// mun_codegen/src/code_gen/context.rs
pub struct CodeGenContext<'db, 'ink> {
    pub context: &'ink Context,
    pub db: &'db dyn mun_hir::HirDatabase,
    pub rust_types: RefCell<HashMap<&'static str, StructType<'ink>>>,
    pub hir_types: HirTypeCache<'db, 'ink>,
    pub optimization_level: inkwell::OptimizationLevel,
    pub target_machine: Rc<TargetMachine>,
}
```

### Module Partitioning

`build_partition` is a tracked function that groups modules into compilation units:

```rust
// mun_codegen/src/module_partition.rs
pub(crate) fn build_partition(db: &dyn CodeGenDatabase) -> Arc<ModulePartition> {
    let mut partition = ModulePartition::default();
    for module in mun_hir::Package::all(db)
        .into_iter()
        .flat_map(|package| package.modules(db))
    {
        let name = if module.name(db).is_some() {
            module.full_name(db)
        } else {
            String::from("mod")
        };
        partition.add_group(db, ModuleGroup::new(db, name, vec![module]));
    }
    Arc::new(partition)
}
```

Each module group maps to one `.munlib` assembly. The partition is cached — it only recomputes when the module structure changes.

## Hot-Reloading Compiler Daemon

The `mun_compiler_daemon` crate connects Salsa's incremental computation to filesystem watching and hot reloading. The core loop:

```rust
// mun_compiler_daemon/src/lib.rs
pub fn compile_and_watch_manifest(
    manifest_path: &Path, config: Config, display_color: DisplayColor,
) -> Result<bool, anyhow::Error> {
    let (package, mut driver) = Driver::with_package_path(manifest_path, config)?;

    // Start filesystem watcher
    let (watcher_tx, watcher_rx) = channel();
    let mut watcher: RecommendedWatcher = Watcher::new(watcher_tx, Duration::from_millis(10))?;
    watcher.watch(&source_directory, RecursiveMode::Recursive)?;

    // Initial compile
    if !driver.emit_diagnostics(&mut stderr(), display_color)? {
        driver.write_all_assemblies(false)?;
    }

    // Watch loop
    while !should_quit.load(Ordering::SeqCst) {
        if let Ok(event) = watcher_rx.recv_timeout(Duration::from_millis(1)) {
            match event {
                Write(ref path) if is_source_file(path) => {
                    let relative_path = compute_source_relative_path(&source_directory, path)?;
                    let file_contents = std::fs::read_to_string(path)?;
                    driver.update_file(relative_path, file_contents);
                    if !driver.emit_diagnostics(&mut stderr(), display_color)? {
                        driver.write_all_assemblies(false)?;
                    }
                }
                Create(ref path) if is_source_file(path) => {
                    driver.add_file(relative_path, file_contents);
                    // ... same pattern
                }
                Remove(ref path) if is_source_file(path) => {
                    driver.remove_file(relative_path);
                    // ...
                }
                Rename(ref from, ref to) => {
                    driver.rename(from_relative_path, to_relative_path);
                    // ...
                }
                _ => {}
            }
        }
    }
    Ok(true)
}
```

### Change-Tracking for Assembly Output

The `Driver` tracks which assemblies have actually changed to avoid unnecessary disk writes:

```rust
// mun_compiler/src/driver.rs
pub struct Driver {
    db: CompilerDatabase,
    out_dir: PathBuf,
    source_root: SourceRoot,
    path_to_file_id: HashMap<RelativePathBuf, FileId>,
    file_id_to_path: HashMap<FileId, RelativePathBuf>,
    next_file_id: usize,
    module_to_temp_assembly_path: HashMap<Module, PathBuf>,
    emit_ir: bool,
}

fn write_target_assembly(&mut self, module: Module, force: bool) -> Result<bool, anyhow::Error> {
    let module_partition = self.db.module_partition();
    let module_group_id = module_partition.group_for_module(module).expect("...");
    let assembly = self.db.target_assembly(module_group_id);

    let assembly_path = self.path_for_module_group(&module_partition[module_group_id])
        .with_extension(TargetAssembly::EXTENSION);

    // Skip write if assembly hasn't changed
    if !force
        && assembly_path.is_file()
        && self.module_to_temp_assembly_path.get(&module).map(AsRef::as_ref)
            == Some(assembly.path())
    {
        return Ok(false);
    }

    assembly.copy_to(&assembly_path)?;
    self.module_to_temp_assembly_path.insert(module, assembly.path().to_path_buf());
    Ok(true)
}
```

The `TargetAssembly` is a `NamedTempFile` — Salsa caches it, and the driver only copies to the output directory when the cached file changes. This enables the runtime to hot-reload only the changed `.munlib` files.

### Filesystem Output Lock

To prevent conflicts between the compiler and the runtime, the driver acquires a filesystem lock:

```rust
fn acquire_filesystem_output_lock(&self) -> lockfile::Lockfile {
    loop {
        match lockfile::Lockfile::create(self.out_dir.join(LOCKFILE_NAME)) {
            Ok(lockfile) => break lockfile,
            Err(_) => std::thread::sleep(Duration::from_secs(1)),
        };
    }
}
```

## Full Pipeline: Source to Hot-Reloadable Binary

```
Source files (watched)
  → driver.update_file() → db.set_file_text()       [Salsa input mutation]
    → db.parse(file_id)                               [AstDatabase]
      → db.item_tree(file_id)                         [DefDatabase]
        → db.package_defs(package_id)                  [DefDatabase]
          → db.infer(def)                              [HirDatabase]
            → db.module_partition()                    [CodeGenDatabase]
              → db.target_assembly(module_group_id)    [CodeGenDatabase — LLVM IR → object → .munlib]
                → driver.write_target_assembly()       [Only if changed — copy to output dir]
                  → Runtime hot-reloads .munlib        [Separate process watches output dir]
```

Each step is a cached Salsa query. Edit one function → only that module's assembly is rebuilt. The rest comes from cache.
