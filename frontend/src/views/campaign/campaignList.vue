<script setup>
import { getCampaign, getCustomersByCampaign, getAgents } from '@/service/campaignservice';
import { onMounted, ref, computed, watch } from 'vue';

const customers = ref([]);
const campaigns = ref([]);

const selectedOption = ref(null); // selected campaign id
const nameFilter = ref('');       // header name search
const statusFilter = ref(null);   // 'pending' | 'success' | 'failed' | null

// load campaigns + agents on mount
onMounted(async () => {
  campaigns.value = await getCampaign();

});

// when campaign changes, fetch customers for that campaign
watch(selectedOption, async (newVal) => {
  if (newVal) {
    customers.value = await getCustomersByCampaign(newVal);
  } else {
    customers.value = [];
  }
});

// status options
const statusOptions = [
  { label: 'Pending', value: 'pending' },
  { label: 'Success', value: 'success' },
  { label: 'Failed', value: 'failed' }
];

// campaign dropdown options
const campaignOptions = computed(() =>
  campaigns.value.map(c => ({
    label: c.name,
    value: c.id
  }))
);

// filters
const filteredCustomers = computed(() => {
  const nameQ = nameFilter.value?.trim().toLowerCase() || '';
  const statusQ = statusFilter.value ? String(statusFilter.value).toLowerCase() : null;

  return (customers.value || []).filter(c => {
    const name = String(c?.name || '').toLowerCase();
    const status = String(c?.status || '').toLowerCase();

    if (nameQ && !name.includes(nameQ)) return false;
    if (statusQ && status !== statusQ) return false;

    return true;
  });
});

function clearFilters() {
  nameFilter.value = '';
  statusFilter.value = null;
}
</script>

<template>
  <div class="card">
    <DataTable
      :value="filteredCustomers"
      paginator
      :rows="10"
      showCurrentPageReport
      paginatorTemplate="CurrentPageReport FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink RowsPerPageDropdown"
      currentPageReportTemplate="Showing {first} to {last} of {totalRecords} entries"
      :rowsPerPageOptions="[10, 25, 50]"
      dataKey="id"
    >
      <!-- Header with campaign + filters -->
      <template #header>
        <div class="flex gap-3 justify-between items-center">
          <div class="flex gap-3 items-center">
            <!-- Campaign dropdown -->
            <Dropdown
              v-model="selectedOption"
              :options="campaignOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Select campaign"
              class="w-64"
            />

            <!-- Name search -->
            <InputText
              v-model="nameFilter"
              placeholder="Search by name"
              class="w-50"
            />

            <!-- Status filter -->
            <Dropdown
              v-model="statusFilter"
              :options="statusOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="All statuses"
              class="w-40"
              showClear
            />

            <Button label="Clear filters" icon="pi pi-times" @click="clearFilters" />
          </div>

            <Button type="button" label="Start" icon="pi pi-play" />
        </div>
      </template>

      <!-- Columns -->
      <Column field="name" header="Customer Name" sortable style="min-width: 200px" />
      <Column field="phone" header="Phone" sortable style="min-width: 150px" />
      <Column field="status" header="Status" sortable style="min-width: 150px">
        <template #body="{ data }">
          <span
            :class="{
              'text-yellow-500 font-medium': (data.status || '').toLowerCase() === 'pending',
              'text-green-600 font-medium': (data.status || '').toLowerCase() === 'success',
              'text-red-500 font-medium': (data.status || '').toLowerCase() === 'failed'
            }"
          >
            {{ data.status }}
          </span>
        </template>
      </Column>
      <Column field="conversation" header="Conversation" style="min-width: 200px" />
    </DataTable>
  </div>
</template>