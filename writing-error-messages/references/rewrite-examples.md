# Rewrite Examples

Open this when rewriting multiple messages, checking whether the skill is behaving correctly, or adding regression examples.

## Product UI Failures

| Before | After | Why |
|--------|-------|-----|
| Something went wrong. | We couldn't save your changes. Check your connection and try again. | Names the failed action and gives a fix. |
| Oops! We hit a snag. | Couldn't publish site. Your changes are saved as a draft. Try publishing again. | Drops cutesy tone, adds reassurance and next action. |
| The upstream service failed to respond. | We couldn't connect to Dropbox. Try reconnecting your account. | Translates jargon into the user-visible service and action. |
| Third-party provider is unavailable. | We couldn't connect your account right now. Try again in a few minutes. | Avoids blame while giving a realistic retry path. |
| Error 500. | We couldn't load your dashboard. Refresh the page. If this keeps happening, contact support with request ID {request_id}. | Keeps diagnostic detail as support context, not the main message. |

## Validation Errors

| Before | After | Why |
|--------|-------|-----|
| Invalid email. | Enter an email address in the format name@example.com. | Explains the expected format. |
| Required field. | Enter a project name. | Names the missing field and action. |
| Illegal date. | Enter a date in the past. | Avoids legalistic wording and says how to fix it. |
| Password not valid. | Password must be at least 12 characters. | Gives the rule. |
| File too large. | Choose a file smaller than 10 MB. | Gives the limit and action. |
| You forgot to select a plan. | Choose a plan. | Avoids blame. |

## Empty States That Are Not Errors

| Before | After | Why |
|--------|-------|-----|
| Error: no results. | No invoices found. Try changing your filters. | Nothing failed; gives a next action. |
| Could not load any tasks. | No tasks yet. Create a task to get started. | Distinguishes empty data from load failure. |
| Invalid search. | No matches for "{query}". Check the spelling or try a broader search. | Uses the search term and suggests recovery. |

## Authentication and Account Recovery

| Before | After | Why |
|--------|-------|-----|
| No account found for this email. | Invalid email or password. | Avoids account enumeration. |
| Password is incorrect for this account. | Invalid email or password. | Avoids confirming account existence. |
| This account is locked. | We couldn't sign you in. Follow the recovery steps or contact support. | Avoids revealing account state while offering help. |
| Email address not registered. | If an account exists for that email address, we'll send password reset instructions. | Safe password-recovery pattern. |

## CLI and Developer-Facing Errors

| Before | After | Why |
|--------|-------|-----|
| Config error. | Could not read config file at ./app.config.toml. Expected TOML, but line 12 is missing a closing quote. Fix the syntax and run `app deploy` again. | Includes file, expectation, received problem, and next command. |
| Bad request. | Could not create project. Field `name` is required. Add `name` to the request body and retry. | Names the failed operation and missing field. |
| ENOENT. | Could not open ./schema.sql because the file does not exist. Check the path or run `app init` to create it. | Translates system error into action. |
| Permission denied. | Could not write to /usr/local/bin. Run the command with a writable install path or choose a user-local directory. | Gives alternatives instead of only naming the failure. |

## Holdout Checks

Use these to test future revisions without overfitting the examples above.

1. A payment submission times out, but the app does not know whether the card was charged.
   - Good output should avoid saying "try again" without duplicate-charge guidance.
   - Good output should tell the user how to check status or contact support.

2. A file upload fails because the file type is unsupported.
   - Good output should name supported file types.
   - Good output should not say "invalid file" alone.

3. A permission error occurs because the user is not an admin.
   - Good output should explain the needed permission if safe.
   - Good output should avoid exposing private resource details.

4. A login attempt fails for an unknown email.
   - Good output should not reveal that the email is unknown.

5. A search returns zero results.
   - Good output should treat it as an empty state, not an error.
