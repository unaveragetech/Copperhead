# Copperhead Roadmap

What we're building next.

---

## Current Status (v0.1.0)

**The full compilation pipeline is verified working.** Python source code is parsed, transpiled to Rust with PyO3 bindings, compiled via Cargo, and produces a `.dll`/`.so` file.

**Working:**
- Full type system (16 primitive types, 4 collection types, 2 ownership types)
- AST parser with type extraction and RPB detection
- Rust transpiler with PyO3 0.23 bindings (supports Python 3.13)
- Complete AST coverage: all 28 statement types, all 27 expression types
- 60+ Python builtins mapped to Rust equivalents
- 40+ string methods mapped (upper, lower, strip, replace, split, find, join, etc.)
- 10+ Vec/Dict methods mapped (append→push, get, keys, values, items, etc.)
- Compiler pipeline: Python → AST → Rust → Cargo → `.dll`/`.so`
- CLI with 10 commands
- AI agent with Ollama integration (verified with real models)
- Module registry with SQLite (13 pre-loaded examples)
- Debugger with syntax/type/pattern/safety checks
- Interactive interpreter (shared workspace for user+AI)
- 375 unit tests (196 AST coverage + 179 core tests, all passing)
- Package builds and publishes to PyPI

**Verified on:**
- Python 3.13.3
- Rust 1.89.0 / Cargo 1.89.0
- PyO3 0.23.5
- Windows 11 (also targets Linux/macOS)

---

## Phase 1: Foundation (Complete)

### v0.1.0 - Initial Release
- [x] Full type system (16 primitives)
- [x] AST parser with type extraction
- [x] Rust transpiler with PyO3 bindings
- [x] Compiler pipeline (parse → transpile → cargo build → `.dll`)
- [x] CLI with 10 commands
- [x] AI agent with Ollama integration
- [x] Module registry with SQLite (13 examples)
- [x] Debugger with syntax/type/pattern checks
- [x] Interactive interpreter
- [x] 179 unit tests + 52 integration tests
- [x] 196 AST coverage tests (all 28 statement types, all 27 expression types)
- [x] 60+ Python builtins mapped to Rust
- [x] 40+ string methods mapped to Rust
- [x] 10+ Vec/Dict methods mapped to Rust
- [x] PyO3 0.23 compatibility (Python 3.13 support)
- [x] Package builds and passes `twine check`
- [x] White paper for non-technical audience
- [x] Complete documentation suite

### v0.1.1 - Polish & Bug Fixes
- [ ] Fix Windows path handling in build output
- [ ] Improve error messages in compiler pipeline
- [ ] Add more test coverage for edge cases
- [ ] Auto-detect and set optimal PyO3 version based on Python version
- [ ] Cache Cargo dependencies across builds

### v0.1.2 - Documentation & DX
- [x] Complete API reference
- [x] Getting started guide
- [x] Tutorial with examples
- [x] Architecture deep dive
- [ ] Video tutorials
- [ ] Interactive playground in docs site
- [ ] Example gallery with live demos

---

## Phase 2: Core Features (Complete)

### v0.2.0 - Enhanced Transpilation
- [x] Python class transpilation
- [x] Lambda function transpilation
- [x] List comprehension support
- [x] Generator/iterator support
- [x] Decorator chain support
- [x] Context manager support (`with` statements)

### v0.2.1 - Advanced Types
- [ ] Generic types (TypeVar)
- [ ] Protocol support
- [ ] Dataclass transpilation
- [ ] Enum support
- [ ] TypedDict support
- [ ] Literal types

### v0.2.2 - Real Function Bodies
- [x] Transpile actual Python function bodies to Rust (not placeholders)
- [x] Support for loops, conditionals, and basic expressions
- [x] Support for function calls and returns
- [x] Support for variable assignment and mutation

---

## Phase 3: AI Agent

### v0.3.0 - Smarter AI
- [x] Context-aware code generation (system prompt with full language reference)
- [x] Registry integration (check existing before generating)
- [x] Ambiguity detection and clarification
- [ ] Multi-file project support
- [ ] Refactoring suggestions
- [ ] Code review capabilities
- [ ] Test generation from code

### v0.3.1 - Agent Collaboration
- [ ] Multi-agent workflows
- [ ] Shared context between agents
- [ ] Agent specialization (types, patterns, etc.)
- [ ] Learning from user patterns
- [ ] Persistent memory across sessions

---

## Phase 4: Performance

### v0.4.0 - Optimization
- [ ] Cross-module inlining
- [ ] Dead code elimination
- [ ] Loop unrolling
- [ ] SIMD vectorization
- [ ] Profile-guided optimization

### v0.4.1 - Caching
- [x] Content-addressable caching (basic)
- [ ] Distributed compilation
- [ ] Remote build cache
- [ ] Build time prediction
- [ ] Cache invalidation strategies

---

## Phase 5: Integration

### v0.5.0 - Library Support
- [ ] NumPy integration
- [ ] Pandas integration
- [ ] Async/await support
- [ ] Context managers
- [ ] Type stubs for popular libraries

### v0.5.1 - IDE Integration
- [ ] VS Code extension
- [ ] PyCharm plugin
- [ ] Real-time type checking
- [ ] Inline performance hints
- [ ] One-click compilation

---

## Phase 6: Production

### v0.6.0 - Enterprise Features
- [ ] License management
- [ ] Usage analytics (opt-in)
- [ ] Cloud compilation
- [ ] Team collaboration
- [ ] CI/CD integration

### v0.6.1 - Distribution
- [x] PyPI packages (wheel + sdist)
- [ ] Docker images
- [ ] Homebrew formula
- [ ] Winget package
- [ ] Snap package

---

## Phase 7: Advanced

### v0.7.0 - Multi-Language
- [ ] C backend (via cffi)
- [ ] WebAssembly output
- [ ] LLVM IR generation
- [ ] Custom backends

### v0.7.1 - Domain Specific
- [ ] Data science DSL
- [ ] Game development DSL
- [ ] Web backend DSL
- [ ] Embedded systems DSL

---

## Long-Term Vision

### Year 1
- Stable v1.0 release
- 1000+ community modules
- Major IDE support
- Production deployments

### Year 2
- Multi-language support
- Cloud-native compilation
- Enterprise adoption
- Performance parity with hand-written Rust

### Year 3
- Standard library extensions
- Hardware acceleration
- Global developer community
- Industry standard for Python performance

---

## How to Contribute

1. **Pick an item** from the roadmap
2. **Open an issue** to discuss your approach
3. **Submit a PR** with tests
4. **Get it reviewed** and merged

### Priority Labels

- **P0**: Critical - blocks other work
- **P1**: High - important for next release
- **P2**: Medium - valuable but not urgent
- **P3**: Low - nice to have

---

## Questions?

Open an issue at [github.com/unaveragetech/copperhead-rust-puthon/issues](https://github.com/unaveragetech/copperhead-rust-puthon/issues)

---

**Last updated:** June 22, 2026
