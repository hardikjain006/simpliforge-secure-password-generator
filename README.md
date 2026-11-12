# Secure Password Generator

## 1. Goal and scope

The repository provides a single `secure-password-generator` command that
generates one cryptographically strong random password per successful run.

Scope for this goal:

- One input mode: command-line arguments only.
- One output mode: the generated password on standard output only.
- Useful `--help` text.
- Predictable errors for all invalid invocations.

Non-goals: password-strength meters, password storage or retrieval,
clipboard integration, configuration files, environment-variable inputs,
interactive prompts, standard-input inputs, server or GUI interfaces, and
multiple generator modes or output formats.

## 2. The one input mode

- The command accepts input only through command-line arguments.
- It MUST NOT read from standard input, prompt interactively, or consult
  configuration files or environment variables for its behavior.
- The only accepted input option is the password length:

  ```sh
  secure-password-generator [--length <n>]
  secure-password-generator [-h | --help]
  ```

- `--length <n>` is optional. When omitted, the length defaults to `16`.
- Only the space-separated form `--length <n>` is accepted. The
  equals-sign form `--length=<n>` (for example `--length=16`) is not an
  accepted spelling of this option and MUST be rejected as an unknown
  option under section 5.
- `--length` MUST be supplied at most once. Supplying `--length` more than
  once (for example `--length 8 --length 16`) is an invalid invocation
  under section 5: empty standard output, exactly one `\n`-terminated
  error line on standard error, exit status `2`. There is no first-wins
  or last-wins resolution.
- `--length` consumes the immediately following argument token as its
  value verbatim, whatever that token's shape, including tokens that begin
  with `-`. For example `--length --foo` means the value is the literal
  token `--foo` and MUST be rejected as a non-integer length under section
  5; it is not a missing value plus an unknown option. A `-h`/`--help`
  token consumed as the `--length` value in this way does NOT trigger help
  output; section 4 help precedence applies only to a `-h`/`--help` token
  that is not consumed as a `--length` value.
- `<n>` lexical form: the value token MUST match `^-?[0-9]+$` exactly (one
  optional leading `-` followed by one or more ASCII digits `0`–`9`, with
  no `+` sign, no fractional part, no unit suffix, and no whitespace
  inside the token; token boundaries are determined by normal shell
  tokenizing, so a quoted `" 16"` is a single token containing a space and
  does not match). Leading zeros are accepted and interpreted as decimal
  (for example `016` means `16`). A token with a leading `+` (for example
  `+16`), embedded whitespace, an empty string, or any other non-matching
  content does not match and MUST be rejected as a non-integer length.
- Classification precedence for `--length` when the option is present:
  1. missing value: no following token exists (a bare trailing `--length`)
     maps to a missing-value error;
  2. otherwise lexical check: a token that does not match `^-?[0-9]+$`
     maps to a non-integer-length error (for example `abc`, `12.5`, `+16`,
     empty string, or `--foo` consumed as the value);
  3. otherwise range check: a matching token whose decimal value is below
     `8` or above `128` maps to an out-of-range-length error (for example
     `-5`, `7`, or `129`).
  Each rejected `--length` invocation maps to exactly one of these three
  categories.
- Accepted range: `8 <= n <= 128` inclusive.
- Any extra positional argument or any unknown option (including the
  `--length=<n>` form) MUST follow the error contract in section 5; the
  success behavior below covers `--length` supplied exactly once or omitted,
  with no other operands.

## 3. The one output mode

- On success the command MUST print exactly one line to standard output:
  the generated password followed by a single trailing newline.
- On success nothing else MUST be written to standard output.
- All diagnostics, help text, and error messages MUST go to standard error,
  except that `--help` output goes to standard output (see section 4).
- The generated password MUST:
  - contain exactly `<n>` characters (or `16` when `--length` is omitted);
  - draw every character from this exact alphabet:

    ```text
    ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()-_=+
    ```

  - be produced with a cryptographically secure random source (for
    example the operating-system CSPRNG). It MUST NOT use a deterministic
    PRNG, a fixed seed, a timestamp-derived seed, or any hard-coded or
    cycling password value.
- Success output is intentionally non-deterministic: two successful runs
  with the same arguments SHOULD normally produce different passwords.
  Tests MUST assert password properties (length and alphabet membership),
  not an exact password value.

## 4. Help text

- `-h` and `--help` MUST print usage information and exit with status `0`
  without generating a password.
- The help text MUST describe:
  - what the command does (generates one secure random password);
  - the `--length` option, its default (`16`), and its accepted range
    (`8`–`128`);
  - the output convention (password on standard output);
  - at least one usage example.
- When a `-h`/`--help` argument token is present and is NOT consumed as the
  value of `--length` (see section 2), help takes precedence over every
  other argument: the command prints help and exits `0` without generating
  a password and without validating `--length`. Examples: `--length 16
  --help` and `--help --length 16` print help and exit `0`, while
  `--length --help` does NOT print help because `--help` is consumed as the
  `--length` value and MUST be rejected as a non-integer length under
  section 5.

## 5. Predictable errors

- Every invalid invocation MUST:
  - write exactly one human-readable error line to standard error,
    terminated by a single `\n`, with no additional usage text or other
    bytes on standard error;
  - write nothing to standard output;
  - exit with status `2`.
- Invalid invocations include, at minimum:
  - `--length` with a non-integer value (for example `abc`, `12.5`,
    `+16`, an empty string, `--foo` consumed as the value, or `--help`
    consumed as the value);
  - `--length` below `8` or above `128` (for example `7`, `129`, or `-5`);
  - `--length` with a missing value (a bare trailing `--length` with no
    following token);
  - `--length` supplied more than once;
  - the equals-sign form `--length=<n>` (for example `--length=16`),
    treated as an unknown option;
  - any other unknown option or any extra positional argument.
- Error messages MUST name the problem (unknown option, missing value,
  non-integer length, or out-of-range length; a repeated `--length` MUST
  instead state that `--length` was supplied more than once) and MUST state
  the accepted range (`8`–`128`) for range violations. No accepted-range
  statement is required for a repeated-`--length` error since it is not a
  range violation.

## 6. Exit-status contract

| Situation              | Stdout          | Stderr           | Exit status |
|------------------------|-----------------|------------------|-------------|
| Success                | password+`\n`   | empty            | `0`         |
| `-h` / `--help`        | help text       | empty            | `0`         |
| Any invalid invocation | empty           | one error line   | `2`         |

- On success, standard error MUST be empty.
- On `-h`/`--help`, standard error MUST be empty.
- On any error, standard output MUST be empty and standard error MUST be
  exactly one `\n`-terminated error line with no usage text.

## 7. Boundary cases (testable)

- Omitted `--length` uses `16` and produces a 16-character password.
- `--length 8` produces an 8-character password (minimum).
- `--length 128` produces a 128-character password (maximum).
- `--length 7`, `--length 129`, and `--length -5` are rejected as
  out-of-range per section 5.
- `--length abc`, `--length 12.5`, `--length +16`, `--length ""` (empty
  string), and `--length " 16"` (inner whitespace) are rejected as
  non-integer per section 5.
- `--length 016` succeeds and produces a 16-character password.
- `--length 8 --length 16` is rejected as a repeated option per section 5.
- `--length=16` is rejected as an unknown option per section 5.
- `--length --foo` is rejected as a non-integer length per section 5
  (`--foo` is consumed verbatim as the value).
- `--length --help` is rejected as a non-integer length per section 5 and
  does NOT print help.
- `--length 16 --help` prints help and exits `0`.
- An unknown flag (for example `--foo`) and an extra positional argument
  (for example `secure-password-generator extra`) are rejected per
  section 5.
- On any error, standard error is exactly one `\n`-terminated line and
  standard output is empty.
- Every character of every successful output belongs to the alphabet in
  section 3.

## 8. Open questions

None. All underspecification in the original goal has been resolved above
with the simplest consistent decisions; no requirement is blocked.
