# Common LLM Failure Patterns

This document captures specific failure patterns observed when using different LLMs to generate Bearer rules. Learning from these helps improve prompts and catch errors early.

## Cross-Model Patterns

These issues appear across multiple LLM models:

### 1. Regex Instead of Bearer Syntax ⚠️

**Frequency**: Very Common (80%+ of first attempts)

**Pattern**: LLMs use regex capture groups instead of Bearer's variable syntax

```yaml
# ❌ WRONG - Regex syntax
pattern: execute\((.+)\)
pattern: (\w+)\.query\("(.*)"\)

# ✅ CORRECT - Bearer syntax
pattern: $<SINK>($<QUERY>)
pattern: $<OBJ>.query($<SQL>)
```

**Why it happens**: LLMs are trained on lots of regex, and the pattern-matching task naturally primes regex thinking.

**Solution**: Explicitly state "Use Bearer's $<VAR> syntax, NOT regex" in the prompt.

---

### 2. Missing Auxiliary Blocks 🔴

**Frequency**: Common (60% of attempts)

**Pattern**: Filters reference detections that don't have auxiliary blocks

```yaml
# ❌ WRONG - References undefined 'sql_sink'
filters:
  - variable: METHOD
    detection: sql_sink
# Missing auxiliary block!

# ✅ CORRECT - Defines the detection
filters:
  - variable: METHOD
    detection: sql_sink
auxiliary:
  sql_sink:
    patterns:
      - pattern: "execute"
```

**Why it happens**: LLMs understand the concept but forget to implement all required pieces.

**Solution**: Include a complete example with auxiliary blocks in the prompt.

---

### 3. Over-Specific Patterns 📍

**Frequency**: Common (50% of attempts)

**Pattern**: Patterns try to match too specifically instead of using filters

```yaml
# ❌ WRONG - Too specific
pattern: ActiveRecord::Base.connection.execute($<SQL>)

# ✅ CORRECT - Broad pattern + filter
pattern: $<OBJ>.$<METHOD>($<SQL>)
filters:
  - variable: METHOD
    detection: sql_methods
```

**Why it happens**: LLMs optimize for precision without considering maintainability.

**Solution**: Emphasize "keep patterns simple, use filters to refine."

---

### 4. Incorrect Sanitizer Syntax ⚠️

**Frequency**: Common (45% of attempts)

**Pattern**: Not using `not:` for sanitizer definitions

```yaml
# ❌ WRONG - Positive match for sanitizer
auxiliary:
  safe_data:
    patterns:
      - pattern: sanitize($<INPUT>)

# ✅ CORRECT - Using 'not:' to exclude
auxiliary:
  tainted:
    patterns:
      - not:
          detection: sanitized
```

**Why it happens**: The double-negative logic is counterintuitive.

**Solution**: Show explicit sanitizer examples with `not:` in prompts.

---

### 5. Wrong Indentation 📏

**Frequency**: Occasional (20% of attempts)

**Pattern**: Using tabs or 4 spaces instead of 2 spaces

```yaml
# ❌ WRONG - 4 spaces or tabs
patterns:
    - pattern: |
        code

# ✅ CORRECT - 2 spaces
patterns:
  - pattern: |
      code
```

**Why it happens**: Different languages have different conventions.

**Solution**: Specify "Use 2-space indentation for YAML."

---

### 6. Missing Required Fields 📋

**Frequency**: Occasional (25% of attempts)

**Pattern**: Omitting message, metadata, or other required fields

```yaml
# ❌ INCOMPLETE
languages: [ruby]
patterns:
  - pattern: code

# ✅ COMPLETE
languages: [ruby]
severity: high
metadata:
  description: "What this detects"
  cwe_id: "89"
patterns:
  - pattern: code
message: "Developer-facing message"
```

**Why it happens**: LLMs focus on the main task and skip boilerplate.

**Solution**: Use a template that includes all required fields.

---

### 7. Language Mismatch 🌐

**Frequency**: Occasional (15% of attempts)

**Pattern**: Generating patterns for wrong language

```yaml
# ❌ WRONG - Java rule with Ruby syntax
languages: [java]
patterns:
  - pattern: execute $<QUERY>  # Ruby-style, no parens

# ✅ CORRECT - Java-appropriate syntax
languages: [java]
patterns:
  - pattern: execute($<QUERY>)
```

**Why it happens**: Context bleeding from examples or training data.

**Solution**: Explicitly state target language multiple times.

---

## Model-Specific Observations

### GPT-4 / GPT-4o

**Strengths**:
- Excellent understanding of security concepts
- Good at explaining reasoning
- Handles complex filter logic well

**Weaknesses**:
- Often uses regex syntax first
- Verbose explanations instead of pure YAML
- Sometimes over-engineers solutions

**Best Practices**:
- Say "Provide ONLY YAML, no explanations"
- Emphasize Bearer syntax explicitly
- Use temperature=0 for consistency

---

### Claude (Opus/Sonnet)

**Strengths**:
- Better at following format instructions
- Good with YAML structure
- Less verbose than GPT-4

**Weaknesses**:
- Sometimes omits auxiliary blocks
- Can be too brief, missing edge cases
- Occasionally forgets framework-specific patterns

**Best Practices**:
- Provide complete template with auxiliary blocks
- Ask for framework-specific considerations
- Request coverage of edge cases

---

### GPT-3.5 Turbo

**Strengths**:
- Fast
- Cheaper for iteration
- Decent for simple patterns

**Weaknesses**:
- Frequently forgets auxiliary blocks
- Struggles with complex filter logic
- More prone to all error patterns

**Best Practices**:
- Use simpler prompts
- Provide very explicit examples
- Expect more revision iterations
- Consider for simple rules only

---

## Detection Strategies

### Automated Checks

Create pre-flight checks for generated rules:

1. **Syntax Check**: Does it use `$<VAR>` not regex?
2. **Completeness**: All required fields present?
3. **Reference Check**: All detections have auxiliary blocks?
4. **YAML Valid**: Proper indentation?
5. **Language Match**: Patterns appropriate for language?

### Manual Review Checklist

- [ ] Uses `$<VAR>` syntax throughout
- [ ] All filters reference existing auxiliary blocks
- [ ] Has `message` field
- [ ] Has `metadata` with `description` and `cwe_id`
- [ ] `cwe_id` is a string
- [ ] `languages` is an array
- [ ] 2-space YAML indentation
- [ ] Patterns match target language syntax
- [ ] Framework-specific if framework specified
- [ ] Includes sanitizer patterns with `not:` if applicable

---

## Recovery Patterns

### When Validation Fails

1. **Parse Error**: Check YAML indentation first
2. **Pattern Not Matching**: Pattern too specific? Add filters instead
3. **Too Many False Positives**: Missing sanitizer auxiliary blocks
4. **Missing Detections**: Pattern too narrow? Broaden and filter
5. **Wrong Language**: Regenerate with explicit language in prompt

### Iterative Refinement

If first generation fails:

1. Identify specific error (use checklist above)
2. Add explicit instruction about that error
3. Show corrected example in prompt
4. Regenerate with enhanced prompt
5. Validate again

---

## Prompt Engineering Learnings

### What Works

✅ Explicit format specification: "Use $<VAR> not regex"
✅ Complete examples with all required fields
✅ Repetition of key constraints
✅ Temperature=0 for deterministic output
✅ "Provide ONLY YAML" to avoid explanations

### What Doesn't Work

❌ Assuming LLM knows Bearer syntax
❌ Vague instructions like "make it good"
❌ Single example without negative examples
❌ Mixing multiple tasks in one prompt
❌ Not specifying indentation

---

## Future Improvements

As we learn more patterns:

1. Add new failure modes to this document
2. Update prompts to prevent known failures
3. Build automated validators for common errors
4. Create language-specific sub-prompts
5. Develop framework-aware templates

---

## Version History

- **2024-12**: Initial version documenting GPT-4 and Claude patterns
- Track major pattern updates here as we discover them
