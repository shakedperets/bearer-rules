# Knowledge Base for Bearer Rule Generation

This directory contains documentation and examples to help generate high-quality Bearer SAST rules using LLMs.

## Structure

```
knowledge/
├── README.md (this file)
├── bearer-syntax-guide.md - Quick reference for Bearer rule syntax
├── llm-failure-patterns.md - Common mistakes LLMs make
└── vulnerabilities/
    ├── sql-injection.md - SQL injection patterns and examples
    └── ... (other vulnerability types)
```

## Purpose

The knowledge base serves multiple purposes:

1. **Context Retrieval**: Documents are indexed and retrieved to provide relevant examples to the LLM during rule generation
2. **Learning Resource**: Documents capture patterns, best practices, and common mistakes
3. **Template Library**: Contains working examples for different vulnerability types and languages

## How to Use

### For Rule Generation

The `ContextAgent` automatically retrieves relevant snippets from this knowledge base based on the specification. These snippets provide:
- Working examples of Bearer rules
- Language-specific patterns
- Framework-specific considerations

### For Adding New Content

When adding new content to the knowledge base:

1. **Use clear, searchable headings**: Help the retrieval system find relevant content
2. **Include code examples**: Provide concrete, working examples
3. **Document patterns**: Explain why certain patterns work or don't work
4. **Language-specific sections**: Separate examples by language for easier retrieval
5. **Link to CWEs**: Reference Common Weakness Enumeration IDs when applicable

### File Naming Convention

- Use lowercase with hyphens: `sql-injection.md`, `path-traversal.md`
- Match vulnerability type slugs used in prompts: `sql_injection` → `sql-injection.md`

## Integration with RAG System

The knowledge base integrates with the RAG (Retrieval-Augmented Generation) system:

1. **Indexing**: Files are loaded by `ContextLoader` from the corpus path
2. **Retrieval**: `ContextRetriever` finds relevant snippets using keyword or semantic search
3. **Prompting**: Retrieved context is passed to `PromptLoader` and included in LLM prompts

## Best Practices

### For Documentation

- Keep examples concise but complete
- Show both vulnerable and safe code patterns
- Include auxiliary blocks in examples (they're often forgotten)
- Document gotchas and edge cases

### For Code Examples

- Use Bearer's `$<VAR>` syntax consistently
- Show proper YAML indentation (2 spaces)
- Include all required fields (languages, severity, metadata, message)
- Demonstrate filter usage
- Show auxiliary block patterns

## Contributing

When you discover:
- A new LLM failure pattern → Add to `llm-failure-patterns.md`
- A useful Bearer syntax pattern → Add to `bearer-syntax-guide.md`
- A vulnerability-specific pattern → Add to `vulnerabilities/<type>.md`

The knowledge base grows organically as we learn what works and what doesn't.
