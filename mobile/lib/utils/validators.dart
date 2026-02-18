bool isValidEmail(String email) =>
    RegExp(r'^[^@]+@[^@]+\.[^@]+$').hasMatch(email);
