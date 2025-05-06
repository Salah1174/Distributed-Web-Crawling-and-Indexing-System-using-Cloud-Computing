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
    const d = new Date().toLocaleDateString()
    date = [d, ...date]
    water = [w, ...water]
    exercise = [e, ...exercise]
    bloodsugar = [b, ...bloodsugar]
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
    // Hide other sections
    document.getElementById("table1").classList.add("hidden");
    document.getElementById("graphSection").classList.add("hidden");

    // Show table2 (Critical Status)
    document.getElementById("table2").classList.remove("hidden");
    populateCriticalStatus(); // You can populate this with data dynamically
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

function displayGraph() {
    // Hide other sections
    document.getElementById("table1").classList.add("hidden");
    document.getElementById("table2").classList.add("hidden");

    // Show graph section
    document.getElementById("graphSection").classList.remove("hidden");
    // Call a function to render the graph, you can use a library like Chart.js
    renderGraph();
    logMessage("User clicked 'Display Graph'");
}

// Populate Instance Info Table
function populateInstanceInfo() {
    const instanceInfo = [
        {
            instanceId: "i-12345678",
            cpuUsage: 30,
            publicIp: "192.168.1.1",
            storageUsage: 80,
            status: "Healthy"
        },
        {
            instanceId: "i-23456789",
            cpuUsage: 60,
            publicIp: "192.168.1.2",
            storageUsage: 90,
            status: "Warning"
        }
    ];

    const output = document.getElementById("instanceInfo");
    output.innerHTML = ""; // Clear existing rows

    instanceInfo.forEach(info => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${info.instanceId}</td>
            <td>${info.cpuUsage}%</td>
            <td>${info.publicIp}</td>
            <td>${info.storageUsage}%</td>
            <td>${info.status}</td>
        `;
        output.appendChild(row);
    });
}

// Populate Critical Status Table
function populateCriticalStatus() {
    const criticalStatus = [
        {
            nodeName: "Node 1",
            cpuUsage: 95,
            storageUsage: 99,
            status: "Critical",
            alert: "High CPU & Storage Usage"
        },
        {
            nodeName: "Node 2",
            cpuUsage: 80,
            storageUsage: 60,
            status: "Warning",
            alert: "High CPU Usage"
        }
    ];

    const output = document.getElementById("criticalStatus");
    output.innerHTML = ""; // Clear existing rows

    criticalStatus.forEach(status => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${status.nodeName}</td>
            <td>${status.cpuUsage}%</td>
            <td>${status.storageUsage}%</td>
            <td>${status.status}</td>
            <td>${status.alert}</td>
        `;
        output.appendChild(row);
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

//not sure?
// async function fetchStats() {
//     try {
//         const response = await fetch('http://44.204.18.153:5000/stats', {
//             method: 'GET',
//             mode: 'cors',
//             cache: 'no-cache'
//         });
//         const data = await response.json();
//         updateStats(data.crawled, data.indexed);
//     } catch (err) {
//         console.error('[Client] Failed to fetch stats:', err);
//     }
// }

// // peridoic call
// setInterval(fetchStats, 5000);