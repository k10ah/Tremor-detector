var socket = io();

var accChart = new Chart(document.getElementById('accChart'), {
    type: 'line',
    data: {
        labels: [],
        datasets: [
            {label:'ax', borderColor:'blue', data:[]},
            {label:'ay', borderColor:'red', data:[]},
            {label:'az', borderColor:'green', data:[]}
        ]
    },
    options: {animation:false, responsive:true, scales:{x:{display:true}, y:{display:true}}}
});

var gyroChart = new Chart(document.getElementById('gyroChart'), {
    type: 'line',
    data: {
        labels: [],
        datasets: [
            {label:'gx', borderColor:'blue', data:[]},
            {label:'gy', borderColor:'red', data:[]},
            {label:'gz', borderColor:'green', data:[]}
        ]
    },
    options: {animation:false, responsive:true, scales:{x:{display:true}, y:{display:true}}}
});

var fftChart = new Chart(document.getElementById('fftChart'), {
    type: 'line',
    data: { labels: [], datasets:[{label:'FFT Energy', borderColor:'purple', data:[]}] },
    options: {animation:false, responsive:true, scales:{x:{display:true}, y:{display:true}}}
});

socket.on('prediction', function(data){
    var time = new Date().toLocaleTimeString();
    // Update charts
    updateChart(accChart, time, [data.ax, data.ay, data.az]);
    updateChart(gyroChart, time, [data.gx, data.gy, data.gz]);
    updateChart(fftChart, time, [data.fft]);
    // Update alert
    var alertBox = document.getElementById('alertBox');
    alertBox.innerHTML = 'Status: ' + data.label + ' | Prob: ' + data.prob;
    if(data.label=='Normal') alertBox.style.backgroundColor = '#90EE90';
    else if(data.label=='Hypoglycemia Tremor') alertBox.style.backgroundColor = '#FF6B6B';
    else alertBox.style.backgroundColor = '#FFD966';
});

function updateChart(chart, label, values){
    chart.data.labels.push(label);
    chart.data.labels = chart.data.labels.slice(-20); // last 20 points
    chart.data.datasets.forEach((dataset, i)=>{
        dataset.data.push(values[i]);
        dataset.data = dataset.data.slice(-20);
    });
    chart.update();
}
