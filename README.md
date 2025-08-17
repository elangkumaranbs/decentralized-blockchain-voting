# 🗳️ Decentralized Blockchain Voting System

A secure, transparent, and immutable voting system built with Django and blockchain technology. This system ensures electoral integrity through decentralized vote recording and real-time verification.

![Python](https://img.shields.io/badge/python-v3.12+-blue.svg)
![Django](https://img.shields.io/badge/django-v4.2+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 🌟 Features

### Core Voting Features
- **🔐 Secure Voter Authentication**: Aadhaar-based voter verification with email OTP
- **📱 Real-time Vote Casting**: Interactive candidate selection with immediate feedback
- **🔗 Blockchain Integration**: Immutable vote recording on blockchain
- **📊 Live Results**: Real-time vote counting and result visualization
- **🛡️ Anti-fraud Protection**: One person, one vote enforcement

### Security Features
- **Multi-factor Authentication**: Aadhaar + Email verification
- **Session Management**: Secure voter session handling
- **Data Encryption**: Sensitive voter data protection
- **Audit Trail**: Complete voting process logging

### User Experience
- **Responsive Design**: Mobile-friendly interface
- **Intuitive UI**: Step-by-step voting process
- **Visual Feedback**: Clear candidate selection and confirmation
- **Accessibility**: User-friendly for all demographics

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- pip (Python package manager)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/decentralized-blockchain-voting.git
   cd decentralized-blockchain-voting
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv .venv
   
   # On Windows
   .venv\Scripts\activate
   
   # On macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create sample data (optional)**
   ```bash
   python create_sample_data.py
   ```

6. **Start the development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   Open your browser and go to `http://127.0.0.1:8000/`

## 📱 Usage

### For Voters

1. **Verification Process**
   - Enter your 12-digit Aadhaar number
   - Verify your email with OTP
   - Access the candidate selection interface

2. **Voting Process**
   - Review candidate profiles and party information
   - Select your preferred candidate
   - Cast your vote securely
   - Receive blockchain confirmation

3. **View Results**
   - Check real-time election results
   - Verify vote transparency

### For Administrators

1. **Voter Management**
   - Add/manage voter registrations
   - Verify voter eligibility
   - Monitor voting statistics

2. **Election Setup**
   - Create voting sessions
   - Manage political parties and candidates
   - Configure election parameters

3. **Results & Analytics**
   - Monitor real-time voting progress
   - Generate detailed reports
   - Audit blockchain records

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Blockchain    │
│   (Django       │◄──►│   (Django       │◄──►│   (Vote         │
│   Templates)    │    │   Views/Models) │    │   Recording)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User          │    │   Database      │    │   Smart         │
│   Interface     │    │   (SQLite)      │    │   Contracts     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📊 Database Schema

### Core Models
- **Voter**: Stores voter information and verification status
- **PoliticalParty**: Manages political parties and candidates
- **Vote**: Records individual votes with blockchain hashes
- **VotingSession**: Manages election periods and configurations
- **VoteRecord**: Blockchain vote records for immutability

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
EMAILJS_PUBLIC_KEY=your-emailjs-public-key
EMAILJS_SERVICE_ID=your-emailjs-service-id
EMAILJS_TEMPLATE_ID=your-emailjs-template-id
```

### Email Configuration
Configure EmailJS for OTP delivery:
1. Create an account at [EmailJS](https://www.emailjs.com/)
2. Set up an email service
3. Create an email template for OTP
4. Update the environment variables

## 🧪 Testing

### Sample Test Data
Use the provided sample data script:
```bash
python create_sample_data.py
```

This creates:
- 6 political parties (BJP, INC, AAP, BSP, SP, TMC)
- 5 test voters with different constituencies
- An active voting session
- Admin user (username: admin, password: admin123)

### Test Aadhaar Numbers
- 123456789012 (Rahul Kumar)
- 234567890123 (Priya Sharma)
- 345678901234 (Amit Singh)
- 456789012345 (Sunita Patel)
- 567890123456 (Rajesh Gupta)

## 🛠️ Technology Stack

### Backend
- **Framework**: Django 4.2+
- **Database**: SQLite (development) / PostgreSQL (production)
- **Authentication**: Custom Aadhaar + Email verification
- **Session Management**: Django sessions

### Frontend
- **Templates**: Django Template Engine
- **Styling**: Bootstrap 5 + Custom CSS
- **JavaScript**: Vanilla JS with modern ES6+
- **Icons**: Font Awesome

### Blockchain
- **Integration**: Custom blockchain client
- **Vote Recording**: Immutable transaction logging
- **Verification**: Cryptographic hash validation

### Communication
- **Email Service**: EmailJS for OTP delivery
- **Real-time Updates**: AJAX for live feedback

## 📁 Project Structure

```
decentralized-blockchain-voting/
├── blockchain/                 # Blockchain integration
│   ├── models.py              # Blockchain vote records
│   ├── blockchain_client.py   # Blockchain interface
│   └── contracts/             # Smart contracts
├── voting/                    # Main voting application
│   ├── models.py             # Core data models
│   ├── views.py              # Application logic
│   ├── urls.py               # URL routing
│   ├── templates/            # HTML templates
│   └── management/           # Custom commands
├── blockchain_voting/         # Project configuration
│   ├── settings.py           # Django settings
│   ├── urls.py              # Main URL configuration
│   └── wsgi.py              # WSGI configuration
├── static/                   # Static files (CSS, JS, images)
├── media/                    # User uploaded files
├── requirements.txt          # Python dependencies
├── manage.py                # Django management script
└── create_sample_data.py     # Sample data generator
```

## 🚀 Deployment

### Local Development
```bash
python manage.py runserver
```

### Production Deployment
1. Set `DEBUG=False` in settings
2. Configure production database (PostgreSQL recommended)
3. Set up static file serving
4. Configure email backend
5. Set up HTTPS

### Docker Deployment (Optional)
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

## 🔒 Security Considerations

- **Data Protection**: Sensitive voter information is encrypted
- **Session Security**: Secure session management with timeout
- **Input Validation**: All user inputs are validated and sanitized
- **CSRF Protection**: Cross-Site Request Forgery protection enabled
- **SQL Injection**: Django ORM provides built-in protection
- **XSS Prevention**: Template auto-escaping enabled

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 coding standards
- Write comprehensive tests
- Update documentation for new features
- Ensure backward compatibility

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Django community for the excellent framework
- Bootstrap team for the responsive UI components
- EmailJS for reliable email delivery service
- Open source blockchain libraries

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/decentralized-blockchain-voting/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/decentralized-blockchain-voting/discussions)
- **Email**: your-email@example.com

## 🗺️ Roadmap

- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Mobile application
- [ ] Integration with more blockchain networks
- [ ] Advanced audit features
- [ ] Voter education modules

---

**⚠️ Disclaimer**: This is a demonstration project for educational purposes. For production use in real elections, additional security audits and compliance with local election laws are required.

**🎯 Made with ❤️ for transparent and secure democratic processes**
