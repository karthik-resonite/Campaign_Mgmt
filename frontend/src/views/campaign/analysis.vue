<template>
  <div class="p-4 max-w-6xl mx-auto">
    <h2 class="mb-4 text-2xl font-semibold">Customer Viewer</h2>

    <!-- Dropdown Row -->
    <div class="flex flex-wrap gap-4 mb-8 items-end">
      <!-- Company Dropdown -->
      <Dropdown
        v-model="selectedCompany"
        :options="companies"
        optionLabel="name"
        placeholder="Select Company"
        filter
        class="w-64"
        @change="onCompanyChange"
      />

      <!-- Campaign Dropdown -->
      <Dropdown
        v-if="campaigns.length"
        v-model="selectedCampaign"
        :options="campaigns"
        optionLabel="name"
        placeholder="Select Campaign"
        filter
        class="w-64"
        @change="onCampaignChange"
      />

      <!-- Agent Dropdown -->
      <Dropdown
        v-if="agents.length"
        v-model="selectedAgent"
        :options="agents"
        optionLabel="name"
        placeholder="Select Agent"
        filter
        class="w-64"
        @change="onAgentChange"
      />
    </div>

    <!-- Customers Table -->
    <div v-if="customers.length">
      <h3 class="mb-3 text-lg font-semibold">Customers of {{ selectedAgent?.name }}</h3>
      <DataTable :value="customers" class="p-datatable-sm" responsiveLayout="scroll">
        <Column field="id" header="ID" />
        <Column field="name" header="Name" />
        <Column field="phone" header="Phone" />
        <Column field="status" header="Status" />
        <Column header="Download Conversation" :headerStyle="{ minWidth: '180px' }">
          <template #body="slotProps">
            <Button
              icon="pi pi-download"
              class="p-button-sm p-button-outlined"
              style="width: 50%"
              @click="downloadConversationCSV(slotProps.data)"
            >
              Download CSV
            </Button>
          </template>
        </Column>
      </DataTable>
    </div>

    <Toast />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import Dropdown from 'primevue/dropdown';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Button from 'primevue/button';
import Toast from 'primevue/toast';
import { useToast } from 'primevue/usetoast';

const toast = useToast();
const API_URL = 'https://redsocks.mu:9000';

// Token + Auth Header
const getToken = () => localStorage.getItem('token');
const authHeaders = () => ({
  headers: {
    Authorization: `Bearer ${getToken()}`
  }
});

// State
const companies = ref([]);
const campaigns = ref([]);
const agents = ref([]);
const customers = ref([]);

const selectedCompany = ref(null);
const selectedCampaign = ref(null);
const selectedAgent = ref(null);

// Fetch Companies on Mount
onMounted(async () => {
  try {
    const res = await axios.get(`${API_URL}/companies/`, authHeaders());
    companies.value = res.data;
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to fetch companies', life: 3000 });
  }
});

// When company selected
const onCompanyChange = async () => {
  selectedCampaign.value = null;
  selectedAgent.value = null;
  campaigns.value = [];
  agents.value = [];
  customers.value = [];

  try {
    const res = await axios.get(`${API_URL}/companies/${selectedCompany.value.id}/campaigns/`, authHeaders());
    campaigns.value = res.data;
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to fetch campaigns', life: 3000 });
  }
};

// When campaign selected
const onCampaignChange = async () => {
  selectedAgent.value = null;
  agents.value = [];
  customers.value = [];

  try {
    const res = await axios.get(`${API_URL}/campaigns/${selectedCampaign.value.id}/agents/`, authHeaders());
    agents.value = res.data;
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to fetch agents', life: 3000 });
  }
};

// When agent selected
const onAgentChange = async () => {
  customers.value = [];

  try {
    const res = await axios.get(`${API_URL}/agents/${selectedAgent.value.id}/customers/`, authHeaders());
    customers.value = res.data;
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to fetch customers', life: 3000 });
  }
};

// Download CSV
const downloadConversationCSV = (customer) => {
  if (!customer.conversations?.length) {
    toast.add({
      severity: 'warn',
      summary: 'No Conversations',
      detail: 'This customer has no conversations.',
      life: 3000
    });
    return;
  }

  let csvContent = "Customer Name,Phone,Conversation ID,Agent ID,Messages\n";

  customer.conversations.forEach(convo => {
    const messagesJson = JSON.stringify(
      convo.messages?.map(msg => ({
        role: msg.role,
        message: msg.message
      }))
    ).replace(/"/g, '""'); // escape quotes for CSV

    const row = [
      `"${customer.name}"`,
      `"${customer.phone}"`,
      `"${convo.conversation_id}"`,
      `"${convo.agent_id}"`,
      `"${messagesJson}"`
    ];

    csvContent += row.join(",") + "\n";
  });

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", `conversation_${customer.phone}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};
</script>
