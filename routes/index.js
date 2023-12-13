const { Router } = require('express');
const multer = require('multer');
const { handleUpload, viewDashboard } = require('../controllers/dashboard');
const {
  viewExperiment,
  viewExperimentResults,
  processResults,
} = require('../controllers/experiments');

const largeFileUpload = multer({
  dest: 'uploads/',
}).fields([
  { name: 'file', maxCount: 1 },
  { name: 'pickleFile', maxCount: 1 },
]);

module.exports = (app) => {
  const dashboardRouter = Router();
  const experimentRouter = Router();

  dashboardRouter.get('/', viewDashboard);

  dashboardRouter.post('/upload', largeFileUpload, handleUpload);

  experimentRouter.get('/:experimentName', viewExperiment);

  experimentRouter.get('/:experimentName/results', viewExperimentResults);

  experimentRouter.get('/:experimentName/results/process', processResults);

  app.use('/', dashboardRouter);
  app.use('/experiments', experimentRouter);
};
