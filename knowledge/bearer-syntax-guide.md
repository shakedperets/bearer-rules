# Bearer SAST Syntax Quick Reference

This guide provides a quick reference for Bearer rule syntax, focusing on common patterns and gotchas.

## Core Syntax

### Variable Captures

Bearer uses special variable syntax, NOT regex:

```yaml
# ✓ CORRECT - Bearer variable syntax
pattern: $<SINK>($<TAINTED>)

# ✗ WRONG - This is regex, not Bearer syntax
pattern: execute\((.+)\)
```

Variables are:
- Named with `$<NAME>` syntax
- Used in filters to reference captured values
- Case-sensitive by convention use UPPERCASE

### Pattern Structure

Patterns should be broad, refined with filters:

```yaml
patterns:
  - pattern: |
      $<OBJ>.$<METHOD>($<ARG>)
    filters:
      - variable: METHOD
        detection: dangerous_methods
      - variable: ARG
        detection: tainted_input
```

### Filters

Filters narrow pattern matches:

```yaml
filters:
  - variable: VARNAME           # Which captured variable
    detection: detector_name    # Which auxiliary block to use
  - variable: ANOTHER
    values:                     # Or match literal values
      - "literal1"
      - "literal2"
```

### Auxiliary Blocks

Define reusable detectors:

```yaml
auxiliary:
  # Positive detector - matches these patterns
  dangerous_methods:
    patterns:
      - pattern: "execute"
      - pattern: "query"
      - pattern: "exec"
  
  # Sanitizer - use 'not:' to exclude safe patterns
  safe_input:
    patterns:
      - not:
          detection: user_input
      - pattern: sanitize($<_>)
```

## Required Fields

Every Bearer rule must have:

```yaml
languages: [ruby]              # Array of languages
severity: high                  # high, medium, or low
metadata:
  description: "What this detects"
  cwe_id: "89"                 # As a string!
patterns:
  - pattern: |
      # pattern content
message: "Message shown to developers"
```

## Common Patterns

### 1. Method Call with Tainted Argument

```yaml
patterns:
  - pattern: |
      $<OBJ>.$<METHOD>($<ARG>)
    filters:
      - variable: METHOD
        detection: sink_methods
      - variable: ARG
        detection: tainted
auxiliary:
  sink_methods:
    patterns:
      - pattern: "execute"
  tainted:
    patterns:
      - not:
          detection: sanitized
```

### 2. String Interpolation

```yaml
patterns:
  - pattern: |
      "$<PREFIX>#{$<VAR>}$<SUFFIX>"
    filters:
      - variable: VAR
        detection: user_input
```

### 3. Binary Operations

```yaml
patterns:
  - pattern: |
      $<LEFT> + $<RIGHT>
    filters:
      - variable: RIGHT
        detection: user_controlled
```

## Language-Specific Notes

### Ruby

```yaml
languages: [ruby]
patterns:
  - pattern: |
      $<OBJ>.$<METHOD> $<ARG>  # Method without parens
  - pattern: |
      $<OBJ>.$<METHOD>($<ARG>) # Method with parens
```

### Java

```yaml
languages: [java]
patterns:
  - pattern: |
      $<OBJ>.$<METHOD>($<ARGS>)  # Always use parens
```

### JavaScript/TypeScript

```yaml
languages: [javascript, typescript]
patterns:
  - pattern: |
      $<OBJ>.$<METHOD>($<ARGS>)
  - pattern: |
      $<FUNC>($<ARGS>)  # Function calls
```

### Python

```yaml
languages: [python]
patterns:
  - pattern: |
      $<OBJ>.$<METHOD>($<ARGS>)
```

## Wildcards and Placeholders

```yaml
$<_>        # Unnamed capture (don't care about value)
$<...>      # Ellipsis - matches any number of arguments
```

Example:
```yaml
pattern: execute($<SQL>, $<...>)  # Matches execute with 1+ args
```

## Negation

Use `not:` for sanitizers:

```yaml
auxiliary:
  safe_data:
    patterns:
      - not:
          detection: tainted_source
      - pattern: sanitize($<_>)
      - pattern: "$<_>.parameterize"
```

## Multiple Patterns

Rules can have multiple top-level patterns:

```yaml
patterns:
  - pattern: |
      # Pattern 1
    filters: [...]
  - pattern: |
      # Pattern 2
    filters: [...]
```

Any match triggers the rule.

## Common Gotchas

1. **Indentation**: Always 2 spaces, not tabs
2. **Strings**: CWE IDs must be strings: `"89"` not `89`
3. **Arrays**: Languages is always an array: `[ruby]` not `ruby`
4. **Auxiliary**: Every referenced detection needs an auxiliary block
5. **Message**: Don't forget the message field!

## Example: Complete SQL Injection Rule

```yaml
languages: [ruby]
severity: high
metadata:
  description: "Detects SQL injection vulnerabilities from unsanitized user input"
  cwe_id: "89"
patterns:
  - pattern: |
      $<OBJ>.$<METHOD>($<SQL>)
    filters:
      - variable: METHOD
        detection: sql_execution
      - variable: SQL
        detection: sql_injection
auxiliary:
  sql_execution:
    patterns:
      - pattern: "execute"
      - pattern: "exec_query"
      - pattern: "select_all"
  sql_injection:
    patterns:
      - pattern: |
          "$<BEFORE>#{$<USER_INPUT>}$<AFTER>"
      - pattern: |
          $<SQL> + $<USER_INPUT>
  user_input:
    patterns:
      - pattern: params
      - pattern: request
message: "Possible SQL injection: unsanitized user input in SQL query"
```

## Resources

- Bearer Docs: https://docs.bearer.com/reference/rules/
- Bearer Rules Repo: https://github.com/Bearer/bearer-rules
- CWE Database: https://cwe.mitre.org/
