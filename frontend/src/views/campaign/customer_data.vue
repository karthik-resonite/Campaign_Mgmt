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
    //loadingAgents.value = true;
    role.value = localStorage.getItem("role");
    generateMonthYearOptions();
    selectedMonthYear.value = getCurrentMonthYear();
    campaigns.value = await getCampaign();
 });

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

  // ? Validation before submit
  if (!selectedOption.value) {
    Toast.add({
      severity: "warn",
      summary: "Missing Campaign",
      detail: "Please select a campaign before submitting.",
      life: 3000,
    });
    return;
  }

  if (!customerFile.value) {
    Toast.add({
      severity: "warn",
      summary: "No File Uploaded",
      detail: "Please upload a CSV or Excel file before submitting.",
      life: 3000,
    });
    return;
  }

  try {
    const formData = new FormData();
    formData.append("name", name.value);
    formData.append("campaign_id", String(selectedOption.value || ""));
    formData.append("company_id", localStorage.getItem("company_id") || "");
    formData.append("agents", "agent_2401k7492tc7emp8kn0mcq71rhah");

    if (customerFile.value) {
      formData.append("csv_file", customerFile.value);
    }

    await RegisterCustomerData(formData);
    resetForm();

    Toast.add({
      severity: "success",
      summary: "Upload Successful",
      detail: "Customer data has been uploaded successfully.",
      life: 3000,
    });

  } catch (err) {
    error.value =
      err?.response?.data?.detail || err?.message || "Error submitting form";

    Toast.add({
      severity: "error",
      summary: "Submission Failed",
      detail: error.value,
      life: 3000,
    });

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





  <!-- Month-Year Selector -->
        <div class="flex flex-row gap-6 items-center justify-center" v-if="role === 'user'">
            <div class="card flex flex-col gap-4 p-6" style="width:100%">

                <span class="text-xl font-bold" style="color: #14648C;">Upload Customer Data</span>
<span class="text-xl font-bold" style="color: #14648C;"></span>
                <!-- Campaign Name -->
                <div class="flex flex-col gap-2">
                    <label for="name">Campaign Name</label>
                    <Dropdown
                        v-model="selectedOption"
                        :options="campaignOptions"
                        optionLabel="label"
                        optionValue="value"
                        placeholder="Select campaign"
                        class="w-full"
                    />
                </div>
                <!-- Agents -->
                <div class="flex flex-col gap-2">
                    <!--<label for="agent-dd">Select Agent</label> -->
                    <!-- <Dropdown id="agent-dd" v-model="selectedAgents" :options="agents" optionLabel="name"
                        optionValue="agent_id" placeholder="Select Agent" class="w-full"  @change="save_name" :loading="loadingAgents"
                        :appendTo="'self'" showClear /> -->
                        <!-- <select 
      v-if="agents && agents.length" 
      v-model="selectedAgents" 
      id="agent-dd" 
      class="role-select" 
      @change="save_name"
  >
      <option 
          v-for="agent in agents" 
          :key="agent.agent_id" 
          :value="agent"
      >
          {{ agent.name }}
      </option>
  </select> -->
  <!-- Optional: show a loading message while agents are null/empty -->
  <!-- <p v-else>Loading agents...</p>
                    <small v-if="!loadingAgents && agents.length === 0" class="text-gray-500">
                        No agents available
                    </small> -->
                </div>
                
                <!-- Gaming Offer 
                <div class="flex flex-col gap-2">
                    <label for="gaming-offer">
                        Select Gaming Offer <span class="text-red-500">*</span>
                    </label>
                    <AutoComplete id="gaming-offer" v-model="gamingOffer" :suggestions="filteredOffers" optionLabel="label"
                        optionValue="value" placeholder="Choose or type offer" @complete="searchOffers" class="w-full"
                        inputClass="w-full" dropdown />
                </div> --> 
                <!-- Agent Name -->
                <div class="flex flex-col gap-2">
                    <!-- <label for="name">Agent Name</label> -->
                    <InputText hidden id="name" v-model="name" type="text" placeholder="Enter your name" />
                </div>
                <!-- Template Download Button -->
                <div class="flex flex-row gap-2 items-center">
                <label>Download Template</label>
                <Button label="Download Excel Template" icon="pi pi-download" severity="success" class="w-fit"
                        @click="downloadTemplate" />
                </div>
                <!-- Drag & Drop Upload -->
                <div
                class="border-2 border-dashed border-gray-400 rounded-lg p-8 text-center cursor-pointer hover:border-blue-500 transition"
                @dragover.prevent
                @dragenter.prevent
                @drop.prevent="handleDrop"
                >
                <i class="pi pi-cloud-upload text-4xl text-blue-500 mb-2"></i>
                <p class="text-gray-600">Drag & drop your CSV/XLSX file here</p>
                <p class="text-gray-500">or</p>
                <Button label="Upload Customers File" icon="pi pi-upload" class="mt-2" @click="$refs.fileInput.click()" />
                <input id="file" ref="fileInput" type="file" accept=".csv,.xlsx" @change="handleFileUpload" class="hidden" />
                </div>
                <!-- File Name -->
                <small v-if="customerFile" class="text-green-600 font-medium">Selected: {{ customerFile.name }}</small>
                <!-- Submit -->
                <div class="flex justify-end">
                <Button label="Submit" icon="pi pi-check" @click="handleSubmit" />
                </div>
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