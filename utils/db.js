const mongoose = require('mongoose');
const { MONGOHOST, MONGOPORT } = require('./constants');

const uri = `mongodb://${MONGOHOST}:${MONGOPORT}`;
mongoose.Promise = global.Promise;

const db = mongoose
  .connect(uri, {
    dbName: 'dashboard',
  })
  .catch((err) => {
    console.log('Error connecting to MongoDB');
    console.log(err);
  });

mongoose.connection.on('connected', () => {
  console.log('Mongoose default connection open');
});

mongoose.connection.on('error', (err) => {
  console.log(`Mongoose default connection error: ${err}`);
});

mongoose.connection.on('disconnected', () => {
  console.log('Mongoose default connection disconnected');
});

process.on('SIGINT', () => {
  mongoose.connection.close(() => {
    console.log(
      'Mongoose default connection disconnected through app termination'
    );
    process.exit(0);
  });
});
