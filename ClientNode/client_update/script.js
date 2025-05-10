// script.js

const editIcon = `<i class="fas fa-edit"></i>`

const deleteIcon = `<i class="fas fa-trash"></i>`

function clearInputs() {
    wInput.value = ""
    eInput.value = ""
    bInput.value = ""
}

function addToLocalStorage(){
    localStorage.setItem("date", JSON.stringify(date))
    localStorage.setItem("water", JSON.stringify(water))
    localStorage.setItem("exercise", JSON.stringify(exercise))
    localStorage.setItem("bloodsugar", JSON.stringify(bloodsugar))
}

function activateEdit(i){
    wInput.value = water[i]
    eInput.value = exercise[i]
    bInput.value = bloodsugar[i]
    editIndex = i
    submitButton.classList.add("hidden")
    editSection.classList.remove("hidden")
}

function cancelEdit() {
    clearInputs()
    editIndex = -1
    submitButton.classList.remove("hidden")
    editSection.classList.add("hidden")
}

function editRow(){
    if(editIndex==-1) return
    water[editIndex] = wInput.value
    exercise[editIndex] = eInput.value
    bloodsugar[editIndex] = bInput.value
    fillTable()
    addToLocalStorage()
    cancelEdit()
}

function deleteRow(i){
    if(!confirm(
    `Confirm that you want to delete the entry: 
    \n ${date[i]}: ${water[i]}ml, ${exercise[i]}min, 
${bloodsugar[i]}mg/dL`)) 
return
    date.splice(i, 1)
    water.splice(i, 1)
    exercise.splice(i, 1)
    bloodsugar.splice(i, 1)
document.querySelector(`#output > tr:nth-child(${i+1})`)
    .classList.add("delete-animation")
    addToLocalStorage()
    setTimeout(fillTable, 500)
}

function fillTable(){
    const tbody = document.getElementById("output")
    const rows = 
        Math.max(water.length, exercise.length, bloodsugar.length)
    let html = ""
    for(let i=0; i<rows; i++){
        let w = water[i] || "N/A"
        let e = exercise[i] || "N/A"
        let b = bloodsugar[i] || "N/A"
        let d = date[i] || "N/A"
        html+=`<tr>
            <td>${d}</td>
            <td>${w}</td>
            <td>${e}</td>
            <td>${b}</td>
            <td>
                <button onclick="activateEdit(${i})" 
                        class="edit">${editIcon}
                </button>
            </td>
            <td>
                <button 
                    onclick="deleteRow(${i})" 
                    class="delete">${deleteIcon}
                </button>
            </td>
        </tr>`        
    }
    tbody.innerHTML = html;
}

let editIndex = -1;

let date = 
    JSON.parse(localStorage.getItem("date")) || []
let water = 
    JSON.parse(localStorage.getItem("water")) || []
let exercise = 
    JSON.parse(localStorage.getItem("exercise")) || []
let bloodsugar = 
    JSON.parse(localStorage.getItem("bloodsugar")) || []

const wInput = document.getElementById("water")
const eInput = document.getElementById("exercise")
const bInput = document.getElementById("bloodsugerlevel")

const submitButton = document.getElementById("submit")
const editSection = document.getElementById("editSection")

fillTable()

submitButton.addEventListener("click", ()=>{
    const w = wInput.value || null;
    const e = eInput.value || null;
    const b = bInput.value || null;
    if(w===null || e===null || b===null) {
        alert("Please enter all the fields.")
        return
    }
    // const d = new Date().toLocaleDateString()
    // date = [d, ...date]
    // water = [w, ...water]
    // exercise = [e, ...exercise]
    // bloodsugar = [b, ...bloodsugar]
    // date.push(d)
    // water.push(w)
    // exercise.push(e)
    // bloodsugar.push(b)
    clearInputs()
    fillTable()
    addToLocalStorage()
})


/*********************Led Status and Drop Down to pick node**********************/
// LED Status and Drop Down to pick node
// for each dropdown
document.querySelectorAll('.custom-dropdown').forEach(container => {
    const btn = container.querySelector('.dropdown-btn');
    const optsContainer = container.querySelector('.dropdown-options');
    const opts = container.querySelectorAll('.option');
    const led  = container.querySelector('.led');
  
    // toggle the options panel
    btn.addEventListener('click', () => {
      optsContainer.classList.toggle('show');
    });
  
    // for each option in this dropdown
    opts.forEach(opt => {
      opt.addEventListener('click', () => {
        const v = opt.dataset.value;
        btn.textContent = opt.textContent;    // update button label
        optsContainer.classList.remove('show');
  
        // update *this* dropdown's LED
        updateLEDStatus(led, v);
      });
    });
  });
  
  // helper to color the LED
  function updateLEDStatus(ledEl, value) {
    if (!ledEl) return;
    if (value === 'option1')       ledEl.style.backgroundColor = 'green';
    else if (value === 'option2')  ledEl.style.backgroundColor = 'red';
    else if (value === 'option3')  ledEl.style.backgroundColor = 'yellow';
  }

  /****************** Populate/Show tables/Graph ************************/


  //logs:
  function logMessage(message) {
    const logOutput = document.getElementById("logOutput");
    const logEntry = document.createElement("div");
    logEntry.textContent = message; // Add the log message
    logOutput.appendChild(logEntry);

    // Scroll to the bottom of the log
    logOutput.scrollTop = logOutput.scrollHeight;
}

function showCriticalStatus() {
  // hide the others
  document.getElementById("table1").classList.add("hidden");
  document.getElementById("graphSection").classList.add("hidden");

  // 1) populate the rows
  populateCriticalStatus();

  // 2) then un‑hide the table if there are any rows
  const hasCritical = 
    document.getElementById("criticalStatus").children.length > 0;
  document.getElementById("table2")
          .classList.toggle("hidden", !hasCritical);

  logMessage("User clicked 'Show Critical Status'");
}


function checkInstanceInfo() {
    // Hide other sections
    document.getElementById("table2").classList.add("hidden");
    document.getElementById("graphSection").classList.add("hidden");

    // Show table1 (Instance Info)
    document.getElementById("table1").classList.remove("hidden");
    populateInstanceInfo(); // You can populate this with data dynamically
    logMessage("User clicked 'Check Instance Info'");
}

function showCriticalStatusIndx() {
  // hide the others
  document.getElementById("table1").classList.add("hidden");
  document.getElementById("graphSection").classList.add("hidden");

  // 1) populate the rows
  populateCriticalStatusIndx();

  // 2) then un‑hide the table if there are any rows
  const hasCritical = 
    document.getElementById("criticalStatus").children.length > 0;
  document.getElementById("table2")
          .classList.toggle("hidden", !hasCritical);

  logMessage("User clicked 'Show Critical Status'");
}


function checkInstanceInfoIndx() {
    // Hide other sections
    document.getElementById("table2").classList.add("hidden");
    document.getElementById("graphSection").classList.add("hidden");

    // Show table1 (Instance Info)
    document.getElementById("table1").classList.remove("hidden");
    populateInstanceInfo(); // You can populate this with data dynamically
    logMessage("User clicked 'Check Instance Info'");
}

function displayGraph() {
    // Hide other sections
    document.getElementById("table1").classList.add("hidden");
    document.getElementById("table2").classList.add("hidden");

    // Show graph section
    document.getElementById("graphSection").classList.remove("hidden");
    // Call a function to render the graph, you can use a library like Chart.js
    populateGraph();
    logMessage("User clicked 'Display Graph'");
}


//populate graph 
let cpuChart = null;

// ─────────────────────────────────────────────────────────────────────────────
// Pick up to 5 nodes: take real‑valued ones first, then fill with N/A ones
function selectFiveForChart() {
  const numeric = crawlers.filter(c => c.cpu_percent != null);
  const na      = crawlers.filter(c => c.cpu_percent == null);

  if (numeric.length >= 5) {
    // last 5 numeric entries
    return numeric.slice(-5);
  } else {
    const needed = 5 - numeric.length;
    const filler = na.slice(-needed);
    return numeric.concat(filler);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Build & render the bar chart
function populateGraph() {
  const chartData = selectFiveForChart();
  const labels    = chartData.map(c => c.ip_address);
  const data      = chartData.map(c => c.cpu_percent != null ? c.cpu_percent : 0);

  const ctx = document.getElementById('cpuGraph').getContext('2d');
  // destroy old chart if exists
  if (cpuChart) cpuChart.destroy();

  cpuChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'CPU Usage (%)',
        data,
        backgroundColor: 'rgba(14,165,233,0.6)',
        borderColor:   'rgba(14,165,233,1)',
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      scales: {
        x: { title: { display: true, text: 'IP Address' } },
        y: {
          title: { display: true, text: 'CPU Usage (%)' },
          min: 0, max: 100
        }
      }
    }
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Swap your displayGraph() to call populateGraph instead of renderGraph
function displayGraph() {
  document.getElementById("table1").classList.add("hidden");
  document.getElementById("table2").classList.add("hidden");
  document.getElementById("graphSection").classList.remove("hidden");

  populateGraph();
  logMessage("User clicked 'Display Graph'");
}









// 1) After buildDropdowns(), also populate both tables
async function fetchAndBuild() {
  try {
    const res  = await fetch(`${API}/crawler-status`);
    const data = await res.json();
    if (!Array.isArray(data) || data.length === 0) {
      console.warn('No crawlers returned');
      return;
    }
    crawlers = data;
    buildDropdowns();

    // now populate both tables
    populateInstanceInfo();
    populateCriticalStatus();

  } catch (err) {
    console.error('Fetch error:', err);
  }
}

// 2) Populate Table 1 with all crawlers

function populateInstanceInfo() {
  const tbody = document.getElementById("instanceInfo");
  tbody.innerHTML = "";                 // clear existing

  crawlers.forEach(c => {
    // derive status text to match LED logic
    const statusText = c.overallStatus === 0
      ? "Offline"
      : c.runningStatus === 0
        ? "Warning"
        : "Healthy";

    // if backend ever returns an instance_id field, use it; else fall back to IP
    const instanceId = c.instance_id || c.ip_address;

    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${instanceId}</td>
      <td>${c.cpu_percent != null ? c.cpu_percent : 'N/A'}%</td>
      <td>${statusText}</td>
    `;
    tbody.appendChild(row);
  });

  // un‑hide the container
  document.getElementById("table1").classList.remove("hidden");
}

// ─────────────────────────────────────────────────────────────────────────────
// 3) Populate Table 2 with only the “red LEDs” (overallStatus===0)

function populateCriticalStatus() {
  const tbody = document.getElementById("criticalStatus");
  tbody.innerHTML = "";

  crawlers
    .filter(c => c.overallStatus === 0)
    .forEach(c => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${c.ip_address}</td>
        <td>${c.cpu_percent != null ? c.cpu_percent : 'N/A'}%</td>
        <td>Critical</td>
        <td>Node offline</td>
      `;

      tbody.appendChild(row);
    });
    
}


//Dummy data graph display 

// Function to render the graph
function renderGraph() {
    const ctx = document.getElementById('cpuGraph').getContext('2d');
    const cpuGraph = new Chart(ctx, {
        type: 'line', // Line chart type
        data: {
            labels: ['0', '1', '2', '3', '4', '5'], // Example time points
            datasets: [{
                label: 'CPU Usage (%)',
                data: [10, 20, 30, 25, 40, 50], // Example CPU usage data, replace this with actual data
                borderColor: '#0ea5e9',
                backgroundColor: 'rgba(14, 165, 233, 0.2)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'CPU Usage (%)'
                    },
                    min: 0,
                    max: 100
                }
            }
        }
    });
}


function fetchNodeData(nodeId) {
    logMessage(`Fetching data for Node ${nodeId}...`);
    // Simulate data fetching
    setTimeout(() => {
        logMessage(`Node ${nodeId} data fetched successfully.`);
        // Assume you're processing data here...
    }, 1000);
}


function updateStats(crawled, indexed) {
    document.getElementById('crawledCount').textContent = crawled;
    document.getElementById('indexedCount').textContent = indexed;
}



function clearResultsContainer() {
    const resultsContainer = document.getElementById('resultsContainer');
    while (resultsContainer.firstChild) {
        resultsContainer.removeChild(resultsContainer.firstChild);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('keywords').addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            document.querySelector('.btn-search').click();
        }
    });
});


document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('sidebar');
    const toggleButton = document.getElementById('toggleSidebar');

    toggleButton.addEventListener('click', (event) => {
        sidebar.classList.toggle('active');
        event.stopPropagation(); 
    });

    document.addEventListener('click', (event) => {
        if (!sidebar.contains(event.target) && !toggleButton.contains(event.target)) {
            sidebar.classList.remove('active');
        }
    });
});


function updateDateTime() {
    const dateElement = document.querySelector('#title-container h6');
    const now = new Date();
    dateElement.textContent = `Date: ${now.toLocaleDateString()}, ${now.toLocaleTimeString()}`;
}
setInterval(updateDateTime,1000); // kol sanya

const API = 'http://3.86.162.149:5001';  // Client IP
let crawlers = [];     // [{ ip_address, runningStatus, overallStatus }, …]
let selectedIps = {};  // Store selected IPs for each dropdown

// Map array index → human label
const labels = ['Main Crawler', 'Crawler#1', 'Crawler#2'];

// Fetch on icon click
document.querySelector('.refresh-icon')
  .addEventListener('click', fetchAndBuild);

// Fetch + build dropdown + light LED
async function fetchAndBuild() {
  try {
    const res  = await fetch(`${API}/crawler-status`);
    const data = await res.json(); // Expect an array
    console.log(data);
    
    if (!Array.isArray(data) || data.length === 0) {
      console.warn('No crawlers returned');
      return;
    }

    crawlers = data;
    buildDropdowns(); // Build dropdowns for each crawler
  } catch (err) {
    console.error('Fetch error:', err);
  }
}

// Build dropdowns for each crawler
function buildDropdowns() {
  const container = document.querySelector('.crawler-container');
  container.innerHTML = '';  // Clear previous crawlers
  
  crawlers.forEach((crawler, idx) => {
    // Create individual dropdown and LED elements for each crawler
    const crawlerDiv = document.createElement('div');
    crawlerDiv.classList.add('custom-dropdown');

    const dropdownLabel = document.createElement('label');
    dropdownLabel.textContent = `Crawler Picker ${idx + 1}`;
    dropdownLabel.classList.add('dropdown-label');

    const dropdownContainer = document.createElement('div');
    dropdownContainer.classList.add('dropdown-container');

    const dropdownBtn = document.createElement('button');
    dropdownBtn.classList.add('dropdown-btn');
    dropdownBtn.textContent = 'Select Crawler';
    dropdownBtn.disabled = true;  // Make button unclickable

    const ledEl = document.createElement('div');
    ledEl.classList.add('led');

    const dropdownOptions = document.createElement('div');
    dropdownOptions.classList.add('dropdown-options');

    // Append elements to the dropdown container
    dropdownContainer.appendChild(dropdownBtn);
    dropdownContainer.appendChild(ledEl);
    dropdownContainer.appendChild(dropdownOptions);

    // Append everything to the main crawler div
    crawlerDiv.appendChild(dropdownLabel);
    crawlerDiv.appendChild(dropdownContainer);

    // Append the crawler div to the main container
    container.appendChild(crawlerDiv);

    // Setup dropdown functionality for this crawler
    setupDropdown(crawler, dropdownBtn, dropdownOptions, ledEl, idx);
  });
}

// Set up the dropdown for each individual crawler
function setupDropdown(crawler, dropdownBtn, dropdownOptions, ledEl, idx) {
  // Build the options based on the crawler's status
  dropdownOptions.innerHTML = '';
  const option = document.createElement('div');
  option.classList.add('option');
  option.dataset.ip = crawler.ip_address;
  option.textContent = labels[idx] || crawler.ip_address;

  option.addEventListener('click', () => {
    selectedIps[crawler.ip_address] = crawler.ip_address;
    dropdownBtn.textContent = option.textContent;
    dropdownOptions.classList.remove('show');
    lightLEDFor(crawler, ledEl);
  });

  dropdownOptions.appendChild(option);

  // Update button text on rebuild
  dropdownBtn.textContent = labels[idx] || crawler.ip_address;

  // Toggle dropdown visibility
  dropdownBtn.addEventListener('click', (e) => {
    e.preventDefault();  // Prevent default action (click)
    dropdownOptions.classList.toggle('show');
  });

  // Light LED based on crawler status
  lightLEDFor(crawler, ledEl);


// If red, enable button and add delete behavior
  if (crawler.overallStatus === 0) {
    dropdownBtn.disabled = false;
    dropdownBtn.addEventListener('click', () => {
      dropdownBtn.closest('.custom-dropdown').remove();
    });
  }
}

// LED coloring helper
function lightLEDFor(crawler, ledEl) {
  if (!crawler || !ledEl) return;

  // your three-state logic for LED color:
  if (crawler.overallStatus === 0) {
    ledEl.style.backgroundColor = 'red';
  } else if (crawler.runningStatus === 0) {
    ledEl.style.backgroundColor = 'yellow';
  } else {
    ledEl.style.backgroundColor = 'green';
  }
}




/* Same for Indexer */

// Feel free to do this differently, whatever best suits your implementation for indexer stats  


let indexers = [];     // [{ ip_address, runningStatus, overallStatus }, …]
let selectedIndxIps = {};  // Store selected IPs for each dropdown

// Map array index → human label
const indexerLabels = ['Indexer#1', 'Indexer#2', 'Indexer#3'];

// Fetch on icon click
document.querySelector('.refresh-icon')
  .addEventListener('click', fetchAndBuildIndx);

// Fetch + build dropdown + light LED
async function fetchAndBuildIndx() {
  try {
    const res  = await fetch(`${API}/crawler-status`); //change the fetch code. Ana msh 3aref enty 3amlah ezay fa saybo
    const data = await res.json(); // Expect an array
    console.log(data);
    
    if (!Array.isArray(data) || data.length === 0) {
      console.warn('No indexers returned');
      return;
    }

    indexers = data;
    buildDropdownsIndx(); // Build dropdowns for each crawler
  } catch (err) {
    console.error('Fetch error:', err);
  }
}

// Build dropdowns for each crawler
function buildDropdownsIndx() {
  const container = document.querySelector('.indexer-container');
  container.innerHTML = '';  // Clear previous indexers
  
  indexers.forEach((indexer, idx) => {
    // Create individual dropdown and LED elements for each crawler
    const indexerDiv = document.createElement('div');
    indexerDiv.classList.add('custom-dropdown');

    const dropdownLabel = document.createElement('label');
    dropdownLabel.textContent = `Indexer Picker ${idx + 1}`;
    dropdownLabel.classList.add('dropdown-label');

    const dropdownContainer = document.createElement('div');
    dropdownContainer.classList.add('dropdown-container');

    const dropdownBtn = document.createElement('button');
    dropdownBtn.classList.add('dropdown-btn');
    dropdownBtn.textContent = 'Select indexer';
    dropdownBtn.disabled = true;  // Make button unclickable

    const ledEl = document.createElement('div');
    ledEl.classList.add('led');

    const dropdownOptions = document.createElement('div');
    dropdownOptions.classList.add('dropdown-options');

    // Append elements to the dropdown container
    dropdownContainer.appendChild(dropdownBtn);
    dropdownContainer.appendChild(ledEl);
    dropdownContainer.appendChild(dropdownOptions);

    // Append everything to the main crawler div
    indexerDiv.appendChild(dropdownLabel);
    indexerDiv.appendChild(dropdownContainer);

    // Append the crawler div to the main container
    container.appendChild(indexerDiv);

    // Setup dropdown functionality for this crawler
    setupDropdownIndx(indexer, dropdownBtn, dropdownOptions, ledEl, idx);
  });
}

// Set up the dropdown for each individual crawler
function setupDropdownIndx(indexer, dropdownBtn, dropdownOptions, ledEl, idx) {
  // Build the options based on the crawler's status
  dropdownOptions.innerHTML = '';
  const option = document.createElement('div');
  option.classList.add('option');
  option.dataset.ip = indexer.ip_address;
  option.textContent = indexerLabels[idx] || indexer.ip_address;

  option.addEventListener('click', () => {
    selectedIndxIps[indexer.ip_address] = indexer.ip_address;
    dropdownBtn.textContent = option.textContent;
    dropdownOptions.classList.remove('show');
    lightLEDForIndx(indexer, ledEl);
  });

  dropdownOptions.appendChild(option);

  // Update button text on rebuild
  dropdownBtn.textContent = indexerLabels[idx] || indexer.ip_address;

  // Toggle dropdown visibility
  dropdownBtn.addEventListener('click', (e) => {
    e.preventDefault();  // Prevent default action (click)
    dropdownOptions.classList.toggle('show');
  });

  // Light LED based on crawler status
  lightLEDForIndx(indexer, ledEl);


// If red, enable button and add delete behavior
  if (indexer.overallStatus === 0) {
    dropdownBtn.disabled = false;
    dropdownBtn.addEventListener('click', () => {
      dropdownBtn.closest('.custom-dropdown').remove();
    });
  }
}

// LED coloring helper
function lightLEDForIndx(indexer, ledEl) {
  if (!indexer || !ledEl) return;

  // your three-state logic for LED color:
  if (indexer.overallStatus === 0) {
    ledEl.style.backgroundColor = 'red';
  } else if (indexer.runningStatus === 0) {
    ledEl.style.backgroundColor = 'yellow';
  } else {
    ledEl.style.backgroundColor = 'green';
  }
}



// Optional: Initial load
fetchAndBuild();

