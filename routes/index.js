const { Router } = require("express");
const multer = require("multer");
const { handleUpload, viewDashboard } = require("../controllers/dashboard");

const largeFileUpload = multer({
  dest: "uploads/",
});

module.exports = (app) => {
  const dashboardRouter = Router();
  const apiRouter = Router();

  dashboardRouter.get("/", viewDashboard);

  dashboardRouter.post("/upload", largeFileUpload.single("file"), handleUpload);

  app.use("/", dashboardRouter);
  app.use("/api", apiRouter);
};
