<script setup>
import { get_Campaign, create_Campaign, make_Calls } from '@/service/campaignservice';
import { onMounted, ref } from 'vue';
import Button from 'primevue/button';
import Tag from 'primevue/tag';
import InputText from 'primevue/inputtext';
import ToastService from 'primevue/toastservice';
import { useToast } from 'primevue/usetoast';

const campaigns = ref([]);
const campaignDialog = ref(false);
const newCampaign = ref({
  name: '',
  email: '',
  status: 'Paused' // default
});
const submitted = ref(false);
const toast = useToast();

// load campaigns on mount
onMounted(async () => {
  const data = await get_Campaign();
  campaigns.value = data.map(c => ({
    ...c,
    status: c.status || 'Paused' // fallback default
  }));
});
// Toggle status
async function toggleStatus(campaign) {
  // Toggle locally
  campaign.status = campaign.status === 'Paused' ? 'Active' : 'Paused';
  console.log('campaign', campaign.id);
  // Only run the function if status is Active
  if (campaign.status === 'Active') {
    try {
      // Example: call your backend or some function
      await make_Calls({ id: campaign.id, type: "campaign" });

      toast.add({
        severity: 'success',
        summary: 'Success',
        detail: 'Campaign activated and function executed',
        life: 2000
      });
    } catch (err) {
      toast.add({
        severity: 'error',
        summary: 'Error',
        detail: err.message || 'Failed to run function',
        life: 3000
      });
      // revert local change on error if needed
      campaign.status = 'Paused';
    }
  }
}

// open create dialog
function openDialog() {
  submitted.value = false;
  newCampaign.value = { name: '', email: '', status: 'Paused' };
  campaignDialog.value = true;
}

// Hide dialog
function hideDialog() {
  campaignDialog.value = false;
}

// Submit new campaign
async function saveCampaign() {
  submitted.value = true;
  if (!newCampaign.value.name || !newCampaign.value.email) return;

  try {
    const created = await create_Campaign(newCampaign.value);
    campaigns.value.push({ ...created, status: created.status || 'Paused' });
    toast.add({ severity: 'success', summary: 'Success', detail: 'Campaign created', life: 3000 });
    hideDialog();
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.message || 'Failed to create campaign', life: 3000 });
  }
}
</script>
<template>
       <div class="flex justify-end mb-3">
      <Button
        label="Create New Campaign"
        icon="pi pi-plus-circle"
        class="p-button-sm"
        style="background-color: #14648C; border: none;"
        @click="openDialog"
      />
    </div>
  <div class="card">
    <DataTable
      :value="campaigns"
      paginator
      :rows="10"
      showCurrentPageReport
      paginatorTemplate="CurrentPageReport FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink RowsPerPageDropdown"
      currentPageReportTemplate="Showing {first} to {last} of {totalRecords} entries"
      :rowsPerPageOptions="[10, 25, 50]"
      dataKey="id"
      class="p-datatable-sm"
    >
      <!-- Campaign Name -->
      <Column field="name" header="Campaign Name" :headerStyle="{ color: '#14648C', minWidth: '200px' }" />
      <!-- Status -->
      <Column header="Status" :headerStyle="{ color: '#14648C', minWidth: '120px' }">
        <template #body="slotProps">
          <Tag
            :value="slotProps.data.status"
            :severity="slotProps.data.status === 'Active' ? 'success' : 'danger'"
            rounded
          />
        </template>
      </Column>
      <!-- Created Date -->
      <Column field="created_at" header="Created Date" :headerStyle="{ color: '#14648C', minWidth: '140px' }">
        <template #body="slotProps">
          {{ new Date(slotProps.data.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) }}
        </template>
      </Column>
      <!-- Calls Made -->
      <!-- <Column field="calls_made" header="Calls Made" :headerStyle="{ color: '#14648C', minWidth: '120px' }" /> -->
       <!-- dummy call made -->
        <Column header="Call Made" :headerStyle="{ color: '#14648C', minWidth: '120px' }">
        <template #body="slotProps">
          {{ slotProps.data.call_made || 0 }}
        </template>
      </Column>
      <!-- Success % -->
      <Column field="success_rate" header="Success %" :headerStyle="{ color: '#14648C', minWidth: '120px' }">
        <template #body="slotProps">
          {{ slotProps.data.success_rate || 0 }}%
        </template>
      </Column>
      <!-- Actions -->
      <!-- Actions -->
<Column header="Actions" :headerStyle="{ color: '#14648C', minWidth: '200px' }">
  <template #body="slotProps">
    <!-- Edit
    <Button
      icon="pi pi-pencil"
      class="p-button-rounded p-button-sm p-button-outlined mr-2"
      severity="info"
      @click="console.log('Edit', slotProps.data)"
    /> -->
    <!-- Pause/Play -->
    <Button
      :icon="slotProps.data.status === 'Paused' ? 'pi pi-play' : 'pi pi-pause'"
      class="p-button-rounded p-button-sm p-button-outlined mr-2"
      :severity="slotProps.data.status === 'Paused' ? 'success' : 'warning'"
      @click="toggleStatus(slotProps.data)"
    />
    <!-- Delete 
    <Button
      icon="pi pi-trash"
      class="p-button-rounded p-button-sm p-button-outlined"
      severity="danger"
      @click="console.log('Delete', slotProps.data)"
    /> -->
  </template>
</Column>
    </DataTable>
      <!-- Dialog -->
  <Dialog v-model:visible="campaignDialog" :style="{ width: '450px' }" header="Create New Campaign" :modal="true">
    <div class="flex flex-col gap-6">
      <div>
        <label for="name" class="block font-bold mb-3">Name</label>
        <InputText id="name" v-model.trim="newCampaign.name" required autofocus :invalid="submitted && !newCampaign.name" fluid />
        <small v-if="submitted && !newCampaign.name" class="text-red-500">Name is required.</small>
      </div>
      <div>
        <label for="email" class="block font-bold mb-3">Email</label>
        <InputText id="email" v-model.trim="newCampaign.email" required :invalid="submitted && !newCampaign.email" fluid />
        <small v-if="submitted && !newCampaign.email" class="text-red-500">Email is required.</small>
      </div>
    </div>

    <template #footer>
      <Button label="Cancel" icon="pi pi-times" text @click="hideDialog" />
      <Button label="Submit" icon="pi pi-check" @click="saveCampaign" />
    </template>
  </Dialog>
  </div>
</template>