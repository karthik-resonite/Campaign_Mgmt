<script setup>
import { ref, onMounted, computed } from 'vue';
import DataView from 'primevue/dataview';
import SelectButton from 'primevue/selectbutton';
import Tag from 'primevue/tag';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import Dialog from 'primevue/dialog';
import Calendar from 'primevue/calendar';
import { useToast } from 'primevue/usetoast';
import { get_Campaign, create_Campaign, make_Calls } from '@/service/campaignservice';
import { useRouter } from 'vue-router'
import { useConfirm } from 'primevue/useconfirm';
const confirm = useConfirm();

const router = useRouter()
const campaigns = ref([]);
const layout = ref('list');
const options = ref(['list', 'grid']);
const toast = useToast();

const campaignDialog = ref(false);
const newCampaign = ref({
  name: '',
  email: '',
  status: 'Paused',
});
const submitted = ref(false);

// ?? Single-date filter state
const filterDate = ref(null);

// Load campaigns on mount
onMounted(async () => {
  const data = await get_Campaign();
  campaigns.value = data.map(c => ({
    ...c,
    status: c.status || 'Paused',
  }));
});

// ?? Computed filtered campaigns (by selected date)
const filteredCampaigns = computed(() => {
  if (!filterDate.value) return campaigns.value;

  const selectedDate = new Date(filterDate.value).toDateString();
  return campaigns.value.filter(campaign => {
    const campaignDate = new Date(campaign.created_at).toDateString();
    return campaignDate === selectedDate;
  });
});

// Toggle campaign status
async function toggleStatus(campaign) {
  const newStatus = campaign.status === 'Paused' ? 'Active' : 'Paused';

  // Ask for confirmation before starting calls
  if (newStatus === 'Active') {
    const confirmed = window.confirm(`Are you sure you want to activate "${campaign.name}" and start calling?`);
    if (!confirmed) return;
  }

  campaign.status = newStatus;

  if (campaign.status === 'Active') {
    try {
      await make_Calls({ id: campaign.id, type: 'campaign' });
      toast.add({ severity: 'success', summary: 'Success', detail: 'Campaign activated', life: 2000 });
    } catch (err) {
      toast.add({ severity: 'error', summary: 'Error', detail: err.message || 'Failed', life: 3000 });
      campaign.status = 'Paused'; // revert on error
    }
  }
}

// Dialog handlers
function openDialog() {
  submitted.value = false;
  newCampaign.value = { name: '', email: '', status: 'Paused' };
  campaignDialog.value = true;
}
function hideDialog() {
  campaignDialog.value = false;
}

// Save new campaign
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

function goToCampaign(id) {
  router.push(`/finearc/customerlist/${id}`)
}
</script>

<template>
  <div class="card">
    <!-- Header -->
    <div class="flex justify-between items-center mb-4 flex-wrap gap-4">
  <h2 class="text-xl font-semibold text-blue-800">Campaigns</h2>
  <div class="flex items-center gap-3 flex-wrap">
    <!-- Layout switch -->
    <SelectButton v-model="layout" :options="options" :allowEmpty="false" />

    <!-- ?? Single Date Filter -->
    <Calendar
      v-model="filterDate"
      dateFormat="yy-mm-dd"
      placeholder="Filter by Date"
      showIcon
      class="p-inputtext-sm"
      v-tooltip="'Filter by Campaigns on the particular date'"
    />

    <!-- ?? Styled Clear Filter Button -->
    <Button
      v-if="filterDate"
      label="Clear Filter"
      icon="pi pi-times"
      class="p-button-sm clear-btn"
      @click="filterDate = null"
      v-tooltip="'Clear Date Filter'"
    />

    <!-- Create campaign -->
    <Button
      label="Create New Campaign"
      icon="pi pi-plus-circle"
      class="p-button-sm"
      style="background-color: #14648C; border: none;"
      @click="openDialog"
    />
  </div>
</div>

<DataView
  :value="filteredCampaigns"
  :layout="layout"
  paginator
  :rows="10"
  dataKey="id"
  class="p-dataview-sm"
>
  <!-- ? List layout -->
  <template #list="{ items }">
    <div class="flex flex-col">
      <div
        v-for="campaign in items"
        :key="campaign.id"
        class="flex flex-col sm:flex-row sm:items-center p-4 border-b border-gray-200 gap-4 hover:bg-gray-50 transition cursor-pointer"
      >
        <!-- Left Content -->
        <div class="flex-1">
          <div class="text-lg font-bold">{{ campaign.name }}</div>
          <div class="text-gray-600">{{ campaign.email }}</div>
          <div class="text-sm text-gray-500">
            Created: {{ new Date(campaign.created_at).toLocaleDateString() }}
          </div>

          <!-- ?? Customer stats -->
          <div class="mt-2 text-sm text-gray-700 flex flex-wrap gap-6 items-center">
            <div class="flex items-center gap-1">
              <i class="pi pi-users"></i>
              <span>{{ campaign.total_customers }}</span>
            </div>
            <div class="flex items-center gap-1 text-green-600 font-medium">
              <span>Interested :</span>
              <span>{{ campaign.interested_customers }}</span>
            </div>
            <div class="flex items-center gap-1 text-red-600 font-medium">
              <span>Not Interested :</span>
              <span>{{ campaign.not_interested_customers }}</span>
            </div>
            <div class="flex items-center gap-1 text-blue-600 font-medium">
              <span>Follow Up :</span>
              <span>{{ campaign.maybe_customers }}</span>
            </div>
          </div>
        </div>

        <!-- Right Buttons -->
        <div class="flex items-center gap-2">
          <Tag
            :value="campaign.status"
            :severity="campaign.status === 'Active' ? 'success' : 'danger'"
            rounded
          />
          <Button
            icon="pi pi-info"
            class="p-button-rounded p-button-sm"
            severity="info"
            @click="goToCampaign(campaign.id)"
          />
          <Button
            :icon="campaign.status === 'Paused' ? 'pi pi-play' : 'pi pi-pause'"
            class="p-button-rounded p-button-sm"
            :severity="campaign.status === 'Paused' ? 'success' : 'warning'"
            @click.stop="toggleStatus(campaign)"
          />
        </div>
      </div>
    </div>
  </template>

  <!-- ? Grid layout -->
  <template #grid="{ items }">
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="campaign in items"
        :key="campaign.id"
        class="p-4 border rounded shadow-sm flex flex-col hover:bg-gray-50 transition cursor-pointer"
      >
        <div class="text-lg font-bold mb-1">{{ campaign.name }}</div>
        <div class="text-gray-600 mb-1">{{ campaign.email }}</div>
        <div class="text-gray-500 mb-3 text-sm">
          Created: {{ new Date(campaign.created_at).toLocaleDateString() }}
        </div>

        <!-- ?? Customer stats -->
        <div class="text-sm text-gray-700 mb-4 flex flex-wrap gap-6 items-center">
          <div class="flex items-center gap-1">
            <i class="pi pi-users"></i>
            <span>{{ campaign.total_customers }}</span>
          </div>
          <div class="flex items-center gap-1 text-green-600 font-medium">
            <span>Interested :</span>
            <span>{{ campaign.interested_customers }}</span>
          </div>
          <div class="flex items-center gap-1 text-red-600 font-medium">
            <span>Not Interested :</span>
            <span>{{ campaign.not_interested_customers }}</span>
          </div>
          <div class="flex items-center gap-1 text-blue-600 font-medium">
            <span>Follow Up :</span>
            <span>{{ campaign.maybe_customers }}</span>
          </div>
        </div>

        <Tag
          :value="campaign.status"
          :severity="campaign.status === 'Active' ? 'success' : 'danger'"
          rounded
          class="mb-3 self-start"
        />

        <div class="flex justify-between items-center">
          <Button
            icon="pi pi-info"
            class="p-button-rounded p-button-sm"
            severity="info"
            @click="goToCampaign(campaign.id)"
          />
          <Button
            :icon="campaign.status === 'Paused' ? 'pi pi-play' : 'pi pi-pause'"
            class="p-button-rounded p-button-sm"
            :severity="campaign.status === 'Paused' ? 'success' : 'warning'"
            @click.stop="toggleStatus(campaign)"
          />
        </div>
      </div>
    </div>
  </template>
</DataView>
    <!-- Create Campaign Dialog -->
    <Dialog v-model:visible="campaignDialog" :style="{ width: '450px' }" header="Create New Campaign" :modal="true">
      <div class="flex flex-col gap-6">
        <div>
          <label for="name" class="block font-bold mb-2">Name</label>
          <InputText
            id="name"
            v-model.trim="newCampaign.name"
            required
            autofocus
            :class="{ 'p-invalid': submitted && !newCampaign.name }"
            style="width: 100%"
          />
          <small v-if="submitted && !newCampaign.name" class="p-error">Name is required.</small>
        </div>
        <div>
          <label for="email" class="block font-bold mb-2">Email</label>
          <InputText
            id="email"
            v-model.trim="newCampaign.email"
            required
            :class="{ 'p-invalid': submitted && !newCampaign.email }"
            style="width: 100%"
          />
          <small v-if="submitted && !newCampaign.email" class="p-error">Email is required.</small>
        </div>
      </div>
      <template #footer>
        <Button label="Cancel" icon="pi pi-times" text @click="hideDialog" />
        <Button label="Submit" icon="pi pi-check" @click="saveCampaign" />
      </template>
    </Dialog>
  </div>
</template>

<style scoped>
.p-invalid {
  border-color: #F44336 !important;
}

/* ?? Custom Clear Filter Button Style */
.clear-btn {
  background-color: #f1f5f9 !important; /* light gray background */
  color: #14648C !important;            /* blue text to match theme */
  border: 1px solid #14648C !important;
  transition: all 0.2s ease;
}

.clear-btn:hover {
  background-color: #14648C !important;
  color: #fff !important;
}
</style>
