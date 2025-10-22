<script setup>
import axios from "axios";
import { ref, onMounted, computed } from "vue";
import { getAgents, RegisterCustomerData, getCampaign, get_dataanalysis } from "../../service/campaignservice";
import Chart from 'primevue/chart';
import { useToast } from 'primevue/usetoast';
const name = ref("");
const email = ref("");
const customerFile = ref(null);
const Toast = useToast();
const gamingOffer = ref(""); // selected or typed offer
const fileInput = ref(null);
const agents = ref([]);           // [{ label, value }]
const selectedAgents = ref(null); // single-select id (or array if multiple)
const loadingAgents = ref(false);
const error = ref("");
const campaigns = ref([]);
const selectedOption = ref(null); // selected campaign id
const role = ref(null);
const callsData = ref(null);
// Predefined offers (could also be fetched from API)
const availableOffers = ref([
    { label: "50% Bonus", value: "50% Bonus" },
    { label: "Free Spins", value: "Free Spins" },
    { label: "VIP Package", value: "VIP Package" }
]);
const metrics_data = ref({
  total_calls: 0,
  success_rate: 0,
  avg_duration:0,
  conversion_rate: 0
});
const selectedMonthYear = ref('');
const monthYearOptions = ref([]);
// AutoComplete suggestions
const filteredOffers = ref([]);
const searchOffers = (event) => {
    if (!event.query.trim().length) {
        filteredOffers.value = [...availableOffers.value];
    } else {
        filteredOffers.value = availableOffers.value.filter((o) =>
            o.label.toLowerCase().includes(event.query.toLowerCase())
        );
    }
};
function normalizeAgents(payload) {
    const list = Array.isArray(payload)
        ? payload
        : Array.isArray(payload?.agents)
            ? payload.agents
            : Array.isArray(payload?.data)
                ? payload.data
                : [];
    return list.map((a) => ({
        label: a.name ?? a.label ?? String(a.id ?? a.value ?? ""),
        value: a.id ?? a.value ?? a.agent_id, // support id/agent_id/value
    }));
}
function getCurrentMonthYear() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
}
function generateMonthYearOptions() {
  const options = [];
  const startYear = 2025;
  const current = new Date();
  const currentYear = current.getFullYear();
  const currentMonth = current.getMonth() + 1;

  for (let y = startYear; y <= currentYear; y++) {
    const maxMonth = y === currentYear ? currentMonth : 12;
    for (let m = 1; m <= maxMonth; m++) {
      const value = `${y}-${String(m).padStart(2, '0')}`;
      const label = `${new Date(y, m - 1).toLocaleString('default', { month: 'long' })} ${y}`;
      options.push({ value, label });
    }
  }
  monthYearOptions.value = options.reverse(); // Recent first
}
onMounted(async () => {
    loadingAgents.value = true;
    role.value = localStorage.getItem("role");
    generateMonthYearOptions();
    selectedMonthYear.value = getCurrentMonthYear();
    get_calllog();
    get_analysis();
    fetchCallsChart();
    try {
        const data = await getAgents();
        console.log('data',data);
        agents.value = data.agents;
        if (agents.value && agents.value.length > 0) {
            // alert('d');  // will trigger now
            selectedAgents.value = agents.value[0]; // pre-select first agent
            name.value = agents.value[0].name; // pre-select first agent
        }
        console.log(agents.value);
        // optional: preselect the first
        // if (agents.value.length) selectedAgents.value = agents.value[0].value;
    } catch (err) {
        console.error("Error fetching agents:", err);
    } finally {
        loadingAgents.value = false;
    }
      campaigns.value = await getCampaign();
});
async function get_analysis() {
  try {
    const response = await get_dataanalysis(selectedMonthYear.value);

    metrics_data.value = {
      total_calls: response.data.total_calls || 0,
      success_rate: response.data.success_rate || 0,
      avg_duration: response.data.avg_duration || 0,
      conversion_rate: response.data.conversion_rate || 0
    };

    //Toast.add({
     // severity: 'success',
      //summary: 'Success',
     // detail: 'Data fetched successfully',
      //life: 3000
   // });
  } catch (err) {
    console.error('Error fetching metrics:', err);
    Toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to fetch metrics',
      life: 3000
    });
  }
}
// campaign dropdown options
const campaignOptions = computed(() =>
  campaigns.value.map(c => ({
    label: c.name,
    value: c.id
  }))
);
const handleFileUpload = (e) => {
    customerFile.value = e.target.files[0];
};
const handleDrop = (e) => {
  const file = e.dataTransfer.files[0]
  if (file && (file.name.endsWith(".csv") || file.name.endsWith(".xlsx"))) {
    customerFile.value = file
  } else {
    alert("Please upload only CSV or Excel files.")
  }
}
const downloadTemplate = () => {
    const link = document.createElement("a");
    link.href = new URL("../../assets/customer_template.xlsx", import.meta.url).href;
    link.download = "customer_template.xlsx";
    link.click();
};
const handleSubmit = async (e) => {
    e.preventDefault();
    error.value = "";
    //if (!gamingOffer.value) {
       // error.value = "Please select a gaming offer.";
        //return;
    //}
    try {
        const formData = new FormData();
        formData.append("name", name.value);
        // formData.append("email", email.value);
        formData.append('campaign_id', String(selectedOption.value || ""))
        formData.append("company_id", localStorage.getItem("company_id") || "");
        formData.append("agents", String(selectedAgents.value.agent_id || ""));
        if (customerFile.value) {
            formData.append("csv_file", customerFile.value);
        }
        //formData.append("gaming_offer",
            //typeof gamingOffer.value === "object" ? gamingOffer.value.value : gamingOffer.value
        //);
        await RegisterCustomerData(formData);
        resetForm();
    } catch (err) {
        error.value =
            err?.response?.data?.detail || err?.message || "Error submitting form";
        console.error(err);
    }
};
const resetForm = () => {
    // name.value = "";
    email.value = "";
    gamingOffer.value = "";
    // selectedAgents.value = null;
    customerFile.value = null;
    selectedOption = null;
    // reset the actual <input type="file">
    if (fileInput.value) {
        fileInput.value.value = "";
    }
};
//const callsData = {
  //labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
 // datasets: [
    //{
     // label: 'Calls',
     // data: [2450, 3120, 2980, 3300],
      //fill: true,
      //borderColor: '#14648C',
      //backgroundColor: 'rgba(20,100,140,0.2)',
     // tension: 0.4
   // }
 // ]
//};

async function fetchCallsChart (){
	
  const res = await axios.get(`https://redsocks.mu:9000/calls-per-week/`);
  callsData.value = res.data;
};

async function get_calllog (){
  const res = await axios.post(`https://redsocks.mu:9000/import-calls/`);
  console.log('calllog',res);
};


const successData = {
  labels: ['Summer', 'Premium', 'Welcome', 'Retention', 'Holiday'],
  datasets: [
    {
      label: 'Success Rate',
      data: [72, 64, 81, 68, 58],
      backgroundColor: '#f97316'
    }
  ]
};
const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    x: {
      offset: true   // Bars centered between ticks
    }
  }
};
const chartOptions1 = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    x: {
      offset: false  // Points sit on ticks
    }
  }
};
function save_name(){
    // alert('hi');
    console.log(selectedAgents.value);
    name.value = selectedAgents.value.name;
}
</script>
<template>
    <div class="p-6 max-w-7xl mx-auto">

        <div class="card flex flex-col gap-6">
<div class="flex justify-between items-center">
  <h2 class="text-2xl font-semibold" style="color: #14648C;">Performance Analysis</h2>

  <!-- Month-Year Selector -->
  <div class="flex gap-4 items-center mb-4">
    <label for="month-year" class="text-lg mt-5 font-medium">Select Month:</label>
    <select v-model="selectedMonthYear" @change="get_analysis" class="border px-3 py-2 rounded mt-5">
      <option v-for="option in monthYearOptions" :key="option.value" :value="option.value">
        {{ option.label }}
      </option>
    </select>
  </div>
</div>
            <div class="flex flex-row gap-6 items-center justify-center">
                <div class="card shadow-none border-0 flex flex-col items-center justify-center gap-4 pe-20 ps-10">
                    <span class="text-4xl font-bold" style="color: #14648C;">{{ metrics_data.total_calls }}</span>
                    <span class="text-gray-600 ">Total Calls</span>
                </div>
                <div class="card shadow-none border-0 flex flex-col items-center justify-center gap-4 px-20">
                    <span class="text-4xl font-bold" style="color: #14648C;">{{metrics_data.success_rate}}%</span>
                    <span class="text-gray-600 whitespace-nowrap">Success Rate</span>
                </div>
                <div class="card shadow-none border-0 flex flex-col items-center justify-center gap-4 px-20">
                    <span class="text-4xl font-bold whitespace-nowrap" style="color: #14648C;">{{metrics_data.avg_duration}}</span>
                    <span class="text-gray-600">Avg. Duration</span>
                </div>
                <div class="card shadow-none border-0 flex flex-col items-center justify-center gap-4 px-10 mb-8" style="margin-bottom: 2rem;">
                    <span class="text-4xl font-bold" style="color: #14648C;">{{metrics_data.conversion_rate}}%</span>
                    <span class="text-gray-600 whitespace-nowrap">Conversion Rate</span>
                </div>
            </div>
            <div class="flex flex-row gap-6">
                
                <div class="card flex flex-col gap-4 p-6 w-1/2" style="width:100%">
                <span class="text-xl font-bold" style="color: #14648C;">Calls Per Day (Last 30 Days)</span>
                <Chart type="line" :data="callsData" :options="chartOptions1" class="h-80" />
                </div>
                
                <!--<div class="card flex flex-col gap-4 p-6 w-1/2" style="margin-bottom: 2rem;">
                <span class="text-xl font-bold" style="color: #14648C;">Success Rate by Campaign</span>
                <Chart type="bar" :data="successData" :options="chartOptions" class="h-80" />
                </div> -->
            </div>
        </div>
            </div>
</template>
<style>
.role-select {
    width: 100%;
    padding: 0.5rem 1rem;
    border-radius: 5px;
    border: 1px solid #ccc;
    font-size: 1rem;
    /* background-color: #fff; */
    transition: border-color 0.3s ease;
}
.role-select:focus {
    outline: none;
    border-color: #4CAF50;
    /* Green border on focus */
}
/* Float label effect when select is focused or value is selected */
.role-select:focus+.float-label-text,
.role-select:not(:placeholder-shown)+.float-label-text {
    top: -10px;
    font-size: 0.85rem;
    color: #4CAF50;
    /* Green label color when focused or selected */
}
</style>