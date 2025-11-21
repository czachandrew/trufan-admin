# Contributing to TruFan

Thank you for your interest in contributing to TruFan! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Follow professional communication standards

## Getting Started

1. **Fork the repository**
2. **Clone your fork**
   ```bash
   git clone https://github.com/your-username/trufan.git
   cd trufan
   ```
3. **Set up development environment**
   ```bash
   make setup
   ```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions or changes

### 2. Make Changes

- Write clean, readable code
- Follow existing code style and conventions
- Add comments for complex logic
- Update documentation as needed

### 3. Write Tests

All new features and bug fixes should include tests:

```bash
# Run tests
make test

# Run with coverage
make test-cov
```

### 4. Follow Code Style

```bash
# Format code with Black
make format

# Check linting
make lint
```

Code style guidelines:
- Use Black for Python formatting
- Maximum line length: 100 characters
- Use type hints where appropriate
- Write descriptive variable and function names

### 5. Commit Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "feat: add parking session management endpoint"
```

Commit message format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Formatting changes
- `refactor:` - Code refactoring
- `test:` - Test changes
- `chore:` - Maintenance tasks

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear description of changes
- Link to related issues
- Screenshots (if UI changes)
- Test results

## Code Review Process

1. All PRs require at least one review
2. Address reviewer feedback
3. Ensure all tests pass
4. Maintain clean commit history

## Testing Guidelines

### Unit Tests

Test individual functions and methods:

```python
def test_password_hashing():
    password = "TestPassword123"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)
```

### Integration Tests

Test API endpoints and workflows:

```python
def test_user_registration(client):
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "TestPass123",
        ...
    })
    assert response.status_code == 201
```

### Test Coverage

- Aim for >80% code coverage
- Test happy paths and edge cases
- Test error handling
- Test authentication and authorization

## Database Changes

When modifying database models:

1. **Update the model** in `backend/app/models/`
2. **Create migration**:
   ```bash
   make migrate-create message="add new field to users"
   ```
3. **Review migration** in `migrations/versions/`
4. **Test migration**:
   ```bash
   make migrate
   ```
5. **Update seed data** if needed in `scripts/seed_data.py`

## API Changes

When adding or modifying endpoints:

1. **Update/create schema** in `backend/app/schemas/`
2. **Update/create service** in `backend/app/services/`
3. **Update/create endpoint** in `backend/app/api/v1/endpoints/`
4. **Add to router** in `backend/app/api/v1/router.py`
5. **Write tests** in `backend/tests/`
6. **Update documentation** in `docs/API.md`

## Documentation

Update documentation when:
- Adding new features
- Changing API endpoints
- Modifying configuration
- Adding dependencies

Documentation locations:
- **README.md** - Main documentation
- **docs/API.md** - API documentation
- **QUICKSTART.md** - Getting started guide
- **Docstrings** - In-code documentation

## Security

Security is critical. When contributing:

- Never commit secrets or API keys
- Follow security best practices
- Report vulnerabilities privately
- Review authentication/authorization carefully
- Validate all user input
- Use parameterized queries
- Follow OWASP guidelines

## Performance

Consider performance implications:

- Use database indexes appropriately
- Implement pagination for large datasets
- Cache frequently accessed data
- Profile slow operations
- Monitor query performance

## Questions?

- **Technical Questions**: Open an issue with the `question` label
- **Bug Reports**: Use the bug report template
- **Feature Requests**: Use the feature request template

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Project documentation

Thank you for contributing to TruFan!
