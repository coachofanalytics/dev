//console.log("This is working!");

(function () {
  var myConnector = tableau.makeConnector();

  myConnector.getSchema = function (schemaCallback) {
    const ratingCols = [
      {
        id: "Rating_Date",
        dataType: tableau.dataTypeEnum.date,
      },
      {
        id: "First_Name",
        dataType: tableau.dataTypeEnum.string,
      },
      {
        id: "Last_Name",
        dataType: tableau.dataTypeEnum.string,
      },
      {
        id: "Topic",
        dataType: tableau.dataTypeEnum.string,
      },
      {
        id: "Punctuality",
        dataType: tableau.dataTypeEnum.int,
      },
      {
        id: "Communication",
        dataType: tableau.dataTypeEnum.int,
      },
      {
        id: "Understanding",
        dataType: tableau.dataTypeEnum.int,
      },
    ];

    let ratingTableSchema = {
      id: "RIVM",
      alias: "Applicants Rating Information Since Start",
      columns: ratingCols,
    };

    schemaCallback([ratingTableSchema]);
  };

  myConnector.getData = function (table, doneCallback) {
    let tableData = [];
    var i = 0;

    $.getJSON(
      // "https://data.rivm.nl/rating-19/COVID-19_aantallen_gemeente_cumulatief.json",
      "https://codatrainingapp.herokuapp.com/application/rating.json",
      function (resp) {
        // Iterate over the JSON object
        for (i = 0, len = resp.length; i < len; i++) {
          tableData.push({
            Rating_Date: resp[i].Rating_Date,
            First_Nane: resp[i].First_Nane,
            Last_Name: resp[i].Last_Name,
            Topic: resp[i].Topic,
            Punctuality: resp[i].Punctuality,
            Communication: resp[i].Communication,
            Understanding: resp[i].Understanding,
          });
        }
        table.appendRows(tableData);
        doneCallback();
      }
    );
  };

  tableau.registerConnector(myConnector);
})();

document.querySelector("#getData").addEventListener("click", getData);

function getData() {
  tableau.connectionName = "Applicants Ratings";
  tableau.submit();
}
