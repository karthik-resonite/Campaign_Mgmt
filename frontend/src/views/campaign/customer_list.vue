<script setup>
import { Service } from '@/service/Services';
import { onMounted, ref, onBeforeUnmount  } from 'vue';
import Button from 'primevue/button';
import Tag from 'primevue/tag';
import Dialog from 'primevue/dialog';
import { useToast } from 'primevue/usetoast';
import { useRoute } from 'vue-router';

const route = useRoute();
const campaignId = ref();

const data = ref([]);
const filteredData = ref([]);
const service = new Service();
const Toast = useToast();
const selectedLeads = ref([]);
const customerInterestFilter = ref('All');

const showCallLogDialog = ref(false);
const callLogsForDialog = ref([]);
const dialogLead = ref(null);
let intervalId = null;

onMounted(() => {
  fetchData();  // Fetch data initially when the component is mounted
  intervalId = setInterval(fetchData, 10000);  // Trigger fetchData every 10 seconds
});


// Cleanup the interval when the component is unmounted
onBeforeUnmount(() => {
  if (intervalId) {
    clearInterval(intervalId);  // Clear the interval when the component is unmounted
  }
});

async function fetchData() {
  try {
    campaignId.value = route.params.id;
    const response = await service.fetch_data(campaignId.value);
    data.value = response.data;
    filteredData.value = [...data.value];
  } catch (err) {
    console.error('Error fetching data:', err);
  }
}

function applyCustomerInterestFilter() {
  const value = customerInterestFilter.value;
  if (value === '' || value === 'All') {
    filteredData.value = [...data.value];
  } else {
    filteredData.value = data.value.filter(item => item.customer_interest === value);
  }
}

async function startcall() {
  Toast.add({ severity: 'info', summary: 'Info', detail: 'Starting calls...', life: 3000 });
  try {
    const response = await service.startcall();
    console.log('response data:', response.data);
  } catch (err) {
    console.error('Error starting call:', err);
  }
}

function downloadCSV(row) {
  const conversations = row.conversations || [];
  if (!conversations.length) {
    Toast.add({ severity: 'warn', summary: 'No Data', detail: 'No conversations available for this lead.', life: 3000 });
    return;
  }

  let csvContent = "data:text/csv;charset=utf-8,Conversation ID,Agent ID,Phone Number,Language,Messages,Created At\n";
  conversations.forEach(convo => {
    const messages = JSON.stringify(convo.messages).replace(/"/g, '""');
    csvContent += `${convo.conversation_id},${convo.agent_id},${convo.phone_number},${convo.language || ''},"${messages}",${convo.created_at}\n`;
  });

  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", `conversations_${row.phone}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

async function deleteLead(row) {
  if (!confirm(`Are you sure you want to delete ${row.name}?`)) {
    return;
  }

  try {
    await service.delete_lead(row.id);
    Toast.add({ severity: 'success', summary: 'Deleted', detail: `${row.name} deleted successfully.`, life: 3000 });
    await fetchData();
  } catch (err) {
    console.error('Error deleting lead:', err);
    Toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to delete lead.', life: 3000 });
  }
}

async function deleteSelected() {
  if (selectedLeads.value.length === 0) {
    Toast.add({ severity: 'warn', summary: 'No Selection', detail: 'Please select at least one lead to delete.', life: 3000 });
    return;
  }

  if (!confirm(`Are you sure you want to delete ${selectedLeads.value.length} leads?`)) {
    return;
  }

  try {
    for (const lead of selectedLeads.value) {
      await service.delete_lead(lead.id);
    }

    Toast.add({ severity: 'success', summary: 'Deleted', detail: `${selectedLeads.value.length} lead(s) deleted successfully.`, life: 3000 });
    selectedLeads.value = [];
    await fetchData();
  } catch (err) {
    console.error('Error deleting leads:', err);
    Toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to delete selected leads.', life: 3000 });
  }
}

function openCallLogDialog(row) {
  dialogLead.value = row;
  callLogsForDialog.value = row.call_logs || [];
  showCallLogDialog.value = true;
}

function closeCallLogDialog() {
  showCallLogDialog.value = false;
  callLogsForDialog.value = [];
  dialogLead.value = null;
}

// Formatting helpers
function formatDateTime(isoString) {
  if (!isoString) return "";
  const dt = new Date(isoString);
  const day = dt.getDate().toString().padStart(2, '0');
  const monthNames = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  const month = monthNames[dt.getMonth()];
  const year = dt.getFullYear();
  const hh = dt.getHours().toString().padStart(2, '0');
  const mm = dt.getMinutes().toString().padStart(2, '0');
  const ss = dt.getSeconds().toString().padStart(2, '0');
  return `${day} ${month} ${year} ${hh}:${mm}:${ss}`;
}

function formatDuration(seconds) {
  if (seconds == null || isNaN(seconds)) {
    return "";
  }
  let s = seconds;
  const hrs = Math.floor(s / 3600);
  s = s % 3600;
  const mins = Math.floor(s / 60);
  const secs = s % 60;
  const parts = [];
  if (hrs) parts.push(`${hrs}hr`);
  if (mins) parts.push(`${mins}min`);
  parts.push(`${secs}sec`);
  return parts.join(' ');
}

function handleCallLogClick(row) {
  if (!row.call_logs || row.call_logs.length === 0) {
    Toast.add({
      severity: 'warn',
      summary: 'No Call Logs',
      detail: 'No call logs found.',
      life: 3000
    })
    return
  }

  openCallLogDialog(row)
}
</script>

<template>
  <div class="card">
    <DataTable
      :value="filteredData"
      paginator
      :rows="10"
      showCurrentPageReport
      paginatorTemplate="CurrentPageReport FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink RowsPerPageDropdown"
      currentPageReportTemplate="Showing {first} to {last} of {totalRecords} entries"
      :rowsPerPageOptions="[10, 25, 50]"
      dataKey="id"
      class="p-datatable-sm"
      :selection="selectedLeads"
      @update:selection="val => selectedLeads = val"
    >
      <template #header>
        <div class="flex justify-end items-end gap-3">
          <div class="flex">
            <i class="pi pi-filter mt-2 pr-2"><b>Customer Interest</b></i>
            <select
              v-model="customerInterestFilter"
              @change="applyCustomerInterestFilter"
              class="p-2 border rounded text-sm"
            >
              <option value="All">All</option>
              <option value="Interested">Interested</option>
              <option value="Not Interested">Not Interested</option>
              <option value="Maybe">Maybe</option>
              <option value="Unknown">Unknown</option>
            </select>
          </div>
          <div>
            <Button
              label="Delete Selected"
              icon="pi pi-trash"
              class="p-button-danger p-button-sm"
              :disabled="selectedLeads.length === 0"
              @click="deleteSelected"
            />
          </div>
        </div>
      </template>

      <Column selectionMode="multiple" headerStyle="width: 3em"></Column>
      <Column field="name" header="Name" :headerStyle="{ color: '#14648C', minWidth: '150px' }" />
      <Column field="phone" header="Phone" :headerStyle="{ color: '#14648C', minWidth: '100px' }" />
      <Column field="source" header="Source" :headerStyle="{ color: '#14648C', minWidth: '100px' }" />

      <Column field="customer_interest" header="Customer Interest" :headerStyle="{ color: '#14648C', minWidth: '140px' }">
        <template #body="slotProps">
          <Tag
            :value="slotProps.data.customer_interest"
            :severity="slotProps.data.customer_interest === 'Interested'
              ? 'success'
              : slotProps.data.customer_interest === 'Not Interested'
              ? 'danger'
              : slotProps.data.customer_interest === 'Maybe'
              ? 'warning'
              : 'info'"
          />
        </template>
      </Column>

      <Column field="status" header="Status" :headerStyle="{ color: '#14648C', minWidth: '140px' }">
        <template #body="slotProps">
          <Tag
            :value="slotProps.data.status"
            :severity="slotProps.data.status === 'Contacted'
              ? 'success'
              : slotProps.data.status === 'Pending'
              ? 'info'
              : 'warning'"
          />
        </template>
      </Column>

      <!-- Call Logs Icon Column -->
      <Column header="Call Logs" :headerStyle="{ color: '#14648C', minWidth: '120px' }">
        <template #body="slotProps">
          <Button
            icon="pi pi-phone"
            class="p-button-rounded p-button-text"
            @click="handleCallLogClick(slotProps.data)"
          />
        </template>
      </Column>

      <Column header="Action" :headerStyle="{ color: '#14648C', minWidth: '180px' }">
        <template #body="slotProps">
          <div class="flex gap-2">
            <Button
              label="Download CSV"
              icon="pi pi-download"
              class="p-button-sm p-button-outlined"
              @click="downloadCSV(slotProps.data)"
            />
            <Button
              label="Delete"
              icon="pi pi-trash"
              class="p-button-sm p-button-danger"
              @click="deleteLead(slotProps.data)"
            />
          </div>
        </template>
      </Column>

    </DataTable>

     <Dialog
      v-model:visible="showCallLogDialog"
      header="Call Logs"
      modal
      :style="{ width: '700px', maxHeight: '80vh' }"
      :breakpoints="{ '1199px': '90vw', '575px': '95vw' }"
      @hide="closeCallLogDialog"
    >
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <h3 style="margin: 0;">Call Logs for {{ dialogLead.name }}</h3>
          <Button icon="pi pi-times" class="p-button-rounded p-button-text" @click="closeCallLogDialog" />
        </div>
      </template>

      <template v-if="dialogLead">
        <div style="margin: 1rem 0;">
          <div><strong>Phone:</strong> {{ dialogLead.phone }}</div>

          <DataTable
            :value="callLogsForDialog"
            :responsiveLayout="'scroll'"
            showGridlines
            class="p-datatable-sm mt-3"
            :emptyMessage="'No call logs available'"
          >
            <Column
              field="to_number"
              header="To"
              :body="row => row.to_number"
            />
            <Column
              field="status"
              header="Status"
              :body="row => row.status"
            />
            <Column
              field="start_time"
              header="Start Time"
              :body="row => formatDateTime(row.start_time)"
            />
            <Column
              field="duration"
              header="Duration"
              :body="row => formatDuration(row.duration)"
            />
          </DataTable>
        </div>
      </template>

      <template #footer>
        <div style="display: flex; justify-content: flex-end;">
          <Button label="Close" icon="pi pi-check" class="p-button-outlined" @click="closeCallLogDialog" />
        </div>
      </template>
    </Dialog>  </div>
</template>
<style scoped>
.p-dialog .p-dialog-content {
  padding: 1.5rem 2rem;
}

/* Alternate row colors */
.p-datatable-sm .p-datatable-tbody > tr:nth-child(even) {
  background-color: #f9f9f9;
}

/* Column cell padding / font tweaks */
.p-datatable-sm .p-datatable-tbody > tr > td {
  padding: 0.5rem 0.75rem;
}

/* Header styling of the call-logs table */
.p-datatable-sm .p-datatable-header {
  background-color: #14648C;
  color: white;
}

.p-datatable-sm .p-datatable-header .p-column-title {
  font-weight: 600;
}

/* Dialog header styling */
.p-dialog .p-dialog-title {
  font-size: 1.25rem;
  font-weight: bold;
}
</style>
