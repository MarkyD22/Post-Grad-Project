from django.contrib.auth.models import User

# Get the user
user = User.objects.get(username='S00044234')

# Set a new password
user.set_password('AccessUser1')  # or whatever password you want
user.save()

print("Password updated for S00044234")

