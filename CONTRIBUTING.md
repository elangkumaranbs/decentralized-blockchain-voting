# Contributing to Decentralized Blockchain Voting System

Thank you for your interest in contributing to our project! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues
1. **Check existing issues** to avoid duplicates
2. **Use issue templates** when available
3. **Provide detailed information**:
   - Operating system and version
   - Python version
   - Steps to reproduce the issue
   - Expected vs actual behavior
   - Screenshots (if applicable)

### Suggesting Features
1. **Open a feature request** issue
2. **Describe the feature** in detail
3. **Explain the use case** and benefits
4. **Provide examples** if possible

### Code Contributions

#### Getting Started
1. **Fork the repository**
2. **Clone your fork**:
   ```bash
   git clone https://github.com/yourusername/decentralized-blockchain-voting.git
   cd decentralized-blockchain-voting
   ```
3. **Set up development environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

#### Development Workflow
1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Make your changes**
3. **Test thoroughly**
4. **Commit with clear messages**:
   ```bash
   git commit -m "Add: feature description"
   ```
5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
6. **Open a Pull Request**

## 📝 Coding Standards

### Python Code Style
- Follow **PEP 8** guidelines
- Use **4 spaces** for indentation
- Maximum **line length of 88 characters**
- Use **meaningful variable names**
- Add **docstrings** for functions and classes

### Django Best Practices
- Use Django's **built-in features** when possible
- Follow **Model-View-Template** pattern
- Use **Django forms** for user input
- Implement proper **error handling**
- Use **Django's security features**

### Frontend Guidelines
- Use **semantic HTML**
- Follow **accessibility standards**
- Use **Bootstrap classes** consistently
- Write **clean, commented JavaScript**
- Ensure **mobile responsiveness**

### Database
- Use **descriptive field names**
- Add **proper indexes** for queries
- Include **migration files**
- Use **Django's ORM** features

## 🧪 Testing Guidelines

### Writing Tests
- Write tests for **all new features**
- Include **edge cases**
- Test **error conditions**
- Maintain **good test coverage**

### Running Tests
```bash
python manage.py test
```

### Test Structure
```python
from django.test import TestCase
from django.contrib.auth.models import User
from voting.models import Voter, Vote

class VoterTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        pass
    
    def test_voter_creation(self):
        """Test voter model creation"""
        pass
```

## 📚 Documentation

### Code Documentation
- Add **docstrings** to all functions and classes
- Use **clear, descriptive comments**
- Document **complex algorithms**
- Include **usage examples**

### README Updates
- Update README for **new features**
- Add **installation steps** if needed
- Include **configuration changes**
- Update **screenshots** if UI changes

## 🔍 Pull Request Guidelines

### Before Submitting
- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Documentation is updated
- [ ] No merge conflicts
- [ ] Commit messages are clear

### PR Description Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass
- [ ] Manual testing completed

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
```

## 🚀 Release Process

### Version Numbering
We use **Semantic Versioning** (SemVer):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Release Steps
1. Update version in `setup.py`
2. Update CHANGELOG.md
3. Create release branch
4. Test thoroughly
5. Merge to main
6. Tag release
7. Deploy to production

## 🛡️ Security

### Reporting Security Issues
- **Do not** open public issues for security vulnerabilities
- **Email** security@example.com with details
- **Include** steps to reproduce
- **Allow time** for fix before disclosure

### Security Guidelines
- Never commit **API keys** or secrets
- Use **environment variables** for configuration
- Implement **proper authentication**
- Validate **all user inputs**
- Use **HTTPS** in production

## 🌟 Recognition

### Contributors
All contributors will be:
- **Listed** in CONTRIBUTORS.md
- **Mentioned** in release notes
- **Credited** in documentation

### Contribution Types
We recognize various types of contributions:
- 💻 **Code**
- 📖 **Documentation**
- 🐛 **Bug Reports**
- 💡 **Ideas & Features**
- 🎨 **Design**
- 🧪 **Testing**
- 🌍 **Translation**

## 📞 Getting Help

### Community Support
- **GitHub Discussions**: General questions and ideas
- **GitHub Issues**: Bug reports and feature requests
- **Email**: technical support

### Development Questions
- Check **existing documentation**
- Search **closed issues**
- Ask in **GitHub Discussions**
- Contact **maintainers** if needed

## 📋 Code of Conduct

### Our Standards
- **Be respectful** and inclusive
- **Welcome newcomers**
- **Give constructive feedback**
- **Focus on the project**
- **Help others learn**

### Enforcement
- **Report issues** to maintainers
- **First offense**: Warning
- **Repeated offenses**: Temporary ban
- **Severe cases**: Permanent ban

## 🎯 Project Goals

### Short-term Goals
- Improve test coverage
- Enhance documentation
- Fix known bugs
- Performance optimization

### Long-term Goals
- Multi-language support
- Mobile application
- Advanced analytics
- Blockchain improvements

## 💡 Tips for New Contributors

### Good First Issues
Look for issues labeled:
- `good first issue`
- `beginner-friendly`
- `documentation`
- `help wanted`

### Learning Resources
- [Django Documentation](https://docs.djangoproject.com/)
- [Python PEP 8](https://www.python.org/dev/peps/pep-0008/)
- [Git Tutorial](https://git-scm.com/docs/gittutorial)
- [GitHub Flow](https://guides.github.com/introduction/flow/)

Thank you for contributing to making voting systems more secure, transparent, and accessible! 🗳️✨
