# AutoGrader-Listener
 HTTP Server which listens for lab submissions, checks validity, then stores submissions in a DB file. This DB file then can be queried for passing or failing grades.

## Project Feature List
Below are some anticipated features. If a feature is not checked off, then it is not completed yet.

### Configuration of HTTP Server
- [ ] Key/Value Parsing: File

### Configuration of File Grading Procedures
- [ ] Key/Value Parsing: File content changes (useful for checking if configuration files contain the correct configuration)
- [ ] Line Parsing: Search for custom line attributes within files (useful for checking logfiles to ensure the correct items are being logged)
- [ ] Hash Verification: Comparison of key file to specified file(s) to validate if an input is correct (useful to check if two files have matching content)

### Grade Reporting Methods
- [ ] CSV Files
- [ ] Encrypted CSV Files
- [ ] Local SQLite Database
- [ ] MySQL Database
- [ ] AWS RDS MySQL