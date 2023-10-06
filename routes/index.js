const { Router } = require('express');
const multer = require('multer');
const { handleUpload, viewDashboard } = require('../controllers/dashboard');
const { viewExperiment } = require('../controllers/experiments');

const largeFileUpload = multer({
  dest: 'uploads/',
});

module.exports = (app) => {
  const dashboardRouter = Router();
  const experimentRouter = Router();

  dashboardRouter.get('/', viewDashboard);

  dashboardRouter.post('/upload', largeFileUpload.single('file'), handleUpload);

  experimentRouter.get('/:experimentName', viewExperiment);

  app.use('/', dashboardRouter);
  app.use('/experiments', experimentRouter);
};
