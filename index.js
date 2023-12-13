const express = require('express');
const app = express();
const port = process.env.PORT || 3000;
const bodyParser = require('body-parser');
const cors = require('cors');

// initialize constants
require('./utils/constants');

// import db just to initialize the connection
require('./utils/db');

const routes = require('./routes');

// setup middlewares
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// setup cors
app.use(
  cors({
    origin: process.env.CORS_ORIGIN || '*', // By default allow all origins
  })
);

// setup template engine
app.set('view engine', 'pug');
app.set('views', './views');

// setup static files
app.use(express.static('public'));

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});

routes(app);
