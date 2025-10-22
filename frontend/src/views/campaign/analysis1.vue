<template>
  <div class="p-4 max-w-4xl mx-auto">
    <h2 class="mb-4 text-xl font-semibold">Companies</h2>
    <ul class="border rounded-md divide-y">
      <li
        v-for="company in companies"
        :key="company.id"
        class="px-4 py-3 cursor-pointer flex justify-between items-center hover:bg-blue-50"
        :class="{ 'bg-blue-100 font-semibold': selectedCompany?.id === company.id }"
        @click="selectCompany(company)"
      >
        <div>
          <h4>{{ company.name }}</h4>
          <p class="text-sm text-gray-600">{{ company.email }}</p>
          <p class="text-sm text-gray-600">{{ company.phone }}</p>
        </div>
        <i class="pi pi-building text-blue-600 text-xl"></i>
      </li>
    </ul>

    <div v-if="campaigns.length" class="mt-8">
      <h3 class="mb-3 text-lg font-semibold">Campaigns for {{ selectedCompany?.name }}</h3>
      <ul class="border rounded-md divide-y">
        <li
          v-for="campaign in campaigns"
          :key="campaign.id"
          class="px-4 py-3 cursor-pointer flex justify-between items-center hover:bg-green-50"
          :class="{ 'bg-green-100 font-semibold': selectedCampaign?.id === campaign.id }"
          @click="selectCampaign(campaign)"
        >
          <div>
            <h4>{{ campaign.name }}</h4>
            <p class="text-sm text-gray-600">{{ campaign.email }}</p>
          </div>
          <i class="pi pi-bullseye text-green-600 text-xl"></i>
        </li>
      </ul>
    </div>

    <div v-if="agents.length" class="mt-8">
      <h3 class="mb-3 text-lg font-semibold">Agents in {{ selectedCampaign?.name }}</h3>
      <ul class="border rounded-md divide-y">
        <li
          v-for="agent in agents"
          :key="agent.id"
          class="px-4 py-3 cursor-pointer flex justify-between items-center hover:bg-yellow-50"
          :class="{ 'bg-yellow-100 font-semibold': selectedAgent?.id === agent.id }"
          @click="selectAgent(agent)"
        >
          <div>
            <h4>{{ agent.name }}</h4>
          </div>
          <i class="pi pi-user text-yellow-600 text-xl"></i>
        </li>
      </ul>
    </div>

    <div v-if="customers.length" class="mt-8">
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import { useToast } from 'primevue/usetoast';
import Button from 'primevue/button';

const toast = useToast();
const API_URL = 'https://redsocks.mu:8000';

const getToken = () => localStorage.getItem('token');
const authHeaders = () => ({
  headers: {
    Authorization: `Bearer ${getToken()}`
  }
});

// Reactive State
const companies = ref([]);
const campaigns = ref([]);
const agents = ref([]);
const customers = ref([]);

const selectedCompany = ref(null);
const selectedCampaign = ref(null);
const selectedAgent = ref(null);

// Fetch all companies
const fetchCompanies = async () => {
  try {
    const res = await axios.get(`${API_URL}/companies/`, authHeaders());
    companies.value = res.data;
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to fetch companies', life: 3000 });
  }
};

// Select a company and fetch its campaigns
const selectCompany = async (company) => {
  selectedCompany.value = company;
  selectedCampaign.value = null;
  selectedAgent.value = null;
  campaigns.value = [];
  agents.value = [];
  customers.value = [];

  try {
    const res = await axios.get(`${API_URL}/companies/${company.id}/campaigns/`, authHeaders());
    campaigns.value = res.data;
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to fetch campaigns', life: 3000 });
  }
};

// Select a campaign and fetch agents
const selectCampaign = async (campaign) => {
  selectedCampaign.value = campaign;
  selectedAgent.value = null;
  agents.value = [];
  customers.value = [];

  try {
    const res = await axios.get(`${API_URL}/campaigns/${campaign.id}/agents/`, authHeaders());
    agents.value = res.data;
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to fetch agents', life: 3000 });
  }
};

// Select an agent and fetch customers
const selectAgent = async (agent) => {
  selectedAgent.value = agent;
  customers.value = [];

  try {
    const res = await axios.get(`${API_URL}/agents/${agent.id}/customers/`, authHeaders());
    customers.value = res.data;
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to fetch customers', life: 3000 });
  }
};

onMounted(() => {
  fetchCompanies();
});

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
    ).replace(/"/g, '""'); // Escape quotes for CSV

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
