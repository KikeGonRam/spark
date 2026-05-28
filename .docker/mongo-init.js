// MongoDB initialization script
// Creates admin user and barberpro database

// Switch to admin database
db = db.getSiblingDB('admin');

// Create admin user
db.createUser({
  user: 'admin',
  pwd: 'password',
  roles: ['root']
});

// Switch to barberpro database
db = db.getSiblingDB('barberpro');

// Create users collection with indexes
db.createCollection('users');
db.users.createIndex({ email: 1 }, { unique: true });
db.users.createIndex({ role: 1 });

print('✓ MongoDB initialization complete');
print('✓ Admin user created');
print('✓ barberpro database created');
print('✓ users collection created with indexes');
