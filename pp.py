import pexpect

# Spawn the child process
child = pexpect.spawn('python3 t59.py')  # Replace 'your_script.py' with your actual script

# Expect the "Enter PEM pass phrase" prompt
child.expect('Enter PEM pass phrase:')

# Send the password
child.sendline('root1234')  # Replace 'your_password' with your actual password

# Continue interacting with the child process as needed
# You can use child.expect(), child.sendline(), and other methods

# Wait for the child process to complete
child.wait()
