const fs = require('fs');

const { SHARED_FOLDER, POST_PROCESSOR_PATH } = require('../utils/constants');
const path = require('path');
const exec = require('child_process').exec;
const readLine = require('readline');
const UserResults = require('../models/userResults');

const getExperimentResults = async (experimentName) => {
  try {
    const experimentResultsPath = `${SHARED_FOLDER}/results/${experimentName}`;

    // check if the folder exists
    if (!fs.existsSync(experimentResultsPath)) {
      return [false, {}];
    }

    const resultCsvPath = `${experimentResultsPath}/result-csv`;
    const combinedOutputPath = `${experimentResultsPath}/combined-output`;

    // check if the folder exists
    if (!fs.existsSync(resultCsvPath)) {
      return [false, {}];
    }

    // check if the folder exists
    if (!fs.existsSync(combinedOutputPath)) {
      return [false, {}];
    }

    const processingInProgress = fs.existsSync(
      `${experimentResultsPath}/processing-in-progress`
    );

    if (processingInProgress) {
      return [false, { message: 'processing in progress' }];
    }

    // read the files in the result-csv folder
    let resultCsvFiles = fs.readdirSync(resultCsvPath);
    // reverse the array so that the latest file is first
    resultCsvFiles = resultCsvFiles.reverse();
    const results = {};

    resultCsvFiles.forEach((resultCsvFile) => {
      const topTenResultsFromEachFile = fs
        .readFileSync(`${resultCsvPath}/${resultCsvFile}`, 'utf8')
        .split('\n')
        .slice(1, 11);

      const splitResults = [];
      topTenResultsFromEachFile.forEach((val) => {
        let [accuracy, recall2, recall4, recall8, avgRank, feature] =
          val.split(',');
        accuracy = Number(accuracy);
        recall2 = Number(recall2);
        recall4 = Number(recall4);
        recall8 = Number(recall8);
        avgRank = Number(avgRank);

        // limit to 4 decimal places
        accuracy = accuracy.toFixed(4);
        recall2 = recall2.toFixed(4);
        recall4 = recall4.toFixed(4);
        recall8 = recall8.toFixed(4);
        avgRank = avgRank.toFixed(4);

        splitResults.push({
          accuracy,
          recall2,
          recall4,
          recall8,
          avgRank,
          feature,
        });
      });
      results[resultCsvFile] = splitResults;
    });

    return [true, results];
  } catch (error) {
    return [false, {}];
  }
};

const postProcessUsingPython = async (experimentName) => {
  try {
    const experimentResultsPath = `${SHARED_FOLDER}/results/${experimentName}`;

    const processingInProgress = fs.existsSync(
      `${experimentResultsPath}/processing-in-progress`
    );

    if (processingInProgress) {
      return [true, 'processing'];
    }

    const addingInProgress = fs.existsSync(
      `${experimentResultsPath}/adding-in-progress`
    );

    if (addingInProgress) {
      return [true, 'adding'];
    }

    // get the path to results (absolute path)
    const resultsPath = path.resolve(experimentResultsPath);

    // start the processing
    const postProcessCommand = `cd ${POST_PROCESSOR_PATH} && python3 getBestFeatures.py ${experimentName} ${resultsPath}`;

    // we won't wait for the command to finish executing
    const postProcessCommandExec = exec(
      postProcessCommand,
      (error, stdout, stderr) => {
        if (error) {
          console.log('error in postProcessUsingPython', error);
          return [false, 'error'];
        }
        console.log('stdout', stdout);
        console.log('stderr', stderr);

        // once processing is done, we'll call readAndAddUserWiseResultsToDb
        readAndAddUserWiseResultsToDb(experimentName);
      }
    );

    return [true, 'processing'];
  } catch (error) {
    console.log('error in postProcessUsingPython', error);
    return [false, 'error'];
  }
};

const addToDbWithSort = async (username, resultsArray) => {
  try {
    const insertFilter = {
      username,
    };

    const insertQuery = {
      $push: {
        results: {
          $each: resultsArray,
          $sort: {
            relativeCoefficient: -1, // sort in descending order
          },
        },
      },
    };

    const insertOptions = {
      upsert: true,
    };

    await UserResults.updateOne(insertFilter, insertQuery, insertOptions);
    return true;
  } catch (error) {
    console.log('error in addToDbWithSort', error);
    return false;
  }
};

const readAndAddUserWiseResultsToDb = async (experimentName) => {
  try {
    const resolvedSharedPath = path.resolve(SHARED_FOLDER);
    // add processing in progress file
    fs.writeFileSync(
      `${SHARED_FOLDER}/results/${experimentName}/adding-in-progress`,
      'processing'
    );

    const filesToRead = fs.readdirSync(
      `${resolvedSharedPath}/results/${experimentName}/user-wise-result`
    );

    for (const file of filesToRead) {
      const username = file.split('.')[0];

      const filestream = fs.createReadStream(
        `${SHARED_FOLDER}/results/${experimentName}/user-wise-result/${file}`
      );

      const rl = readLine.createInterface({
        input: filestream,
        crlfDelay: Infinity,
      });

      let linesRead = 0;
      let resultsArray = [];
      // read the file line by line
      for await (const line of rl) {
        linesRead += 1;
        if (linesRead === 1) {
          continue; // skip the first line (headers)
        }

        let [
          relativeCoefficient,
          ipGuessed,
          file,
          feature,
          accuracy,
          recallAt2,
          recallAt4,
          recallAt8,
          avgRank,
        ] = line.split(',');
        relativeCoefficient = Number(relativeCoefficient);
        resultsArray.push({
          experimentName,
          relativeCoefficient,
          ipGuessed,
          file,
          feature,
          accuracy,
          recallAt2,
          recallAt4,
          recallAt8,
          avgRank,
        });

        if (linesRead % 500 === 0) {
          await addToDbWithSort(username, resultsArray); // add to db every 500 lines
          resultsArray = [];
        }
      }
    }

    // remove processing in progress file
    fs.unlinkSync(
      `${SHARED_FOLDER}/results/${experimentName}/adding-in-progress`
    );

    // delete the user-wise-result folder
    fs.rmdirSync(
      `${SHARED_FOLDER}/results/${experimentName}/user-wise-result`,
      { recursive: true }
    );
  } catch (error) {
    console.log('error in readAndAddUserWiseResultsToDb', error);
    return false;
  }
};

module.exports = {
  getExperimentResults,
  postProcessUsingPython,
  readAndAddUserWiseResultsToDb,
};
