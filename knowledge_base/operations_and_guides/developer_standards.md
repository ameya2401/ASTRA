# Developer Standards & Conventions

> Engineering rules, coding conventions, and architectural constraints across the ASTRA codebase.

Every contributor and AI agent working on ASTRA must adhere strictly to these engineering standards.

---

## 1. Golden Architectural Rules

1. **Error-Tolerant Parsing**: When processing incoming code diffs, always use Tree-sitter's error-tolerant parser (`has_error` handling). Never allow a malformed syntax node from an agent PR to crash the triage service.
2. **Thread-Safe Singleton Resources**: Heavy neural models (`SentenceEmbedder`) and gradient-boosted trees must be initialized once via singletons protected with thread locks. Never reload models in request loops.
3. **Strict Type Hints & Async Discipline**: All core models use SQLAlchemy 2.0 mapped columns and Pydantic v2 schemas. Database sessions must use the `@asynccontextmanager` async session factory. Never use synchronous blocking I/O in FastAPI routes.
4. **No Destructive Git Operations**: Never run `git push --force`, `git reset --hard`, or `git clean -fd` without explicit instruction.
5. **Clean Repository Hygiene**: Never commit `.env`, `data/*.db`, `test_reports/`, `models/*.pt`, or `__pycache__` to git.
6. **Mandatory Knowledge Base Updates**: Whenever implementing any phase, feature, bugfix, or update inside the project, you must update the `knowledge_base/` folder with complete, accurate information, schemas, formulas, and code references.

---

## 2. Things to Avoid

- **Do NOT use Python's built-in `ast` module**: All AST parsing must use `tree-sitter` and `tree-sitter-python` for cross-language compatibility and syntax error resilience.
- **Do NOT use raw line diffs for risk calculations**: Plain text line counts (`+10/-2`) are blind to AST structure. Always compute structural node churn.
- **Do NOT reload models per request**: Loading MiniLM or XGBoost on every PR webhook introduces severe latency spikes. Use cached module-level singletons.
- **Do NOT claim completion without running verification gates**: Always run and display the test output before claiming a task or milestone is done.

---

## 3. Communication & Style Guidelines

- **No em dashes ("--")**: Do not use em dashes in written documentation or code comments. Use commas, periods, or plain hyphens.
- **No AI puffery or robotic vocabulary**: Avoid robotic filler words ("leverage", "delve", "pivotal", "testament", "crucial", "robust", "underscores"). Write plain, concrete, and active sentences.
- **Clickable links**: Always format file and symbol references as clickable markdown links using the `file://` scheme.
