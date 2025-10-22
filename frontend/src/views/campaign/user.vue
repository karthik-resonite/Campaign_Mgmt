<template>
  <div class="card">
    <div class="flex justify-end mb-3 gap-2">
      <Button label="Add User" icon="pi pi-plus" @click="showAddDialog = true" />
    </div>

    <DataTable :value="companies" dataKey="id" class="p-datatable-sm">
      <Column field="name" header="Organisation Name" />
      <Column field="username" header="Username" />
      <Column field="email" header="Email" />
      <Column field="phone" header="Phone" />
      <Column field="role" header="Role" />

      <Column header="Actions" style="width: 150px">
        <template #body="{ data }">
          <Button
            icon="pi pi-pencil"
            class="p-button-sm p-button-text"
            @click="openEditDialog(data)"
            tooltip="Edit User"
          />
        </template>
      </Column>
    </DataTable>

    <!-- Add User Dialog -->
    <Dialog style="width:350px" v-model:visible="showAddDialog" header="Add New User" modal>
      <div class="p-fluid">
        <div class="field flex flex-col mb-3">
          <label for="name">Organisation Name</label>
          <InputText id="name" v-model="newCompany.name" />
        </div>
        <div class="field flex flex-col mb-3">
          <label for="username">Username</label>
          <InputText id="username" v-model="newCompany.username" />
        </div>
        <div class="field flex flex-col mb-3">
          <label for="email">Email</label>
          <InputText id="email" v-model="newCompany.email" />
        </div>
        <div class="field flex flex-col mb-3">
          <label for="phone">Phone</label>
          <InputText id="phone" v-model="newCompany.phone" />
        </div>
        <div class="field flex flex-col mb-3">
          <label for="password">Password</label>
          <InputText id="password" type="password" v-model="newCompany.password" />
        </div>
      </div>

      <template #footer>
        <Button label="Cancel" icon="pi pi-times" class="p-button-text" @click="showAddDialog = false" />
        <Button label="Save" icon="pi pi-check" @click="createCompany" />
      </template>
    </Dialog>

    <!-- Edit User Dialog -->
    <Dialog style="width:350px" v-model:visible="showEditDialog" header="Edit User" modal>
      <div class="p-fluid">
        <div class="field flex flex-col mb-3">
          <label for="edit-name">Organisation Name</label>
          <InputText id="edit-name" v-model="editCompany.name" />
        </div>
        <div class="field flex flex-col mb-3">
          <label for="edit-username">Username</label>
          <InputText id="edit-username" v-model="editCompany.username" />
        </div>
        <div class="field flex flex-col mb-3">
          <label for="edit-email">Email</label>
          <InputText id="edit-email" v-model="editCompany.email" />
        </div>
        <div class="field flex flex-col mb-3">
          <label for="edit-phone">Phone</label>
          <InputText id="edit-phone" v-model="editCompany.phone" />
        </div>
      </div>

      <template #footer>
        <Button label="Cancel" icon="pi pi-times" class="p-button-text" @click="showEditDialog = false" />
        <Button label="Update" icon="pi pi-check" @click="updateCompany" />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { useToast } from 'primevue/usetoast';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import Dialog from 'primevue/dialog';

const toast = useToast();
const API_URL = 'https://redsocks.mu:9000';
const getToken = () => localStorage.getItem('token');
const authHeaders = () => ({
  headers: {
    Authorization: `Bearer ${getToken()}`
  }
});

const companies = ref([]);
const showAddDialog = ref(false);
const showEditDialog = ref(false);

const newCompany = ref({
  name: '',
  username: '',
  email: '',
  phone: '',
  password: '',
  role: 'user'
});

const editCompany = ref({
  id: null,
  name: '',
  username: '',
  email: '',
  phone: '',
  role: ''
});

const fetchCompanies = async () => {
  try {
    const res = await axios.get(`${API_URL}/companies/`, authHeaders());
    companies.value = res.data;
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load users', life: 3000 });
  }
};

const createCompany = async () => {
  // Validate required fields
  const { name, username, email, phone, password, role } = newCompany.value;
  if (!name || !username || !email || !phone || !password || !role) {
    toast.add({
      severity: 'warn',
      summary: 'Missing Fields',
      detail: 'Please fill in all the fields',
      life: 3000
    });
    return; // Stop execution if validation fails
  }

  try {
    await axios.post(`${API_URL}/companies/`, newCompany.value, authHeaders());
    toast.add({ severity: 'success', summary: 'Created', detail: 'User created successfully', life: 3000 });
    showAddDialog.value = false;
    newCompany.value = { name: '', username: '', email: '', phone: '', password: '', role: 'user' };
    await fetchCompanies();
  } catch (err) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: err.response?.data?.detail || 'Failed to create user',
      life: 3000
    });
  }
};

const openEditDialog = (company) => {
  editCompany.value = { ...company }; // shallow copy to avoid direct mutation
  showEditDialog.value = true;
};

const updateCompany = async () => {
  // Validate required fields
  const { name, username, email, phone, role } = editCompany.value;
  if (!name || !username || !email || !phone || !role) {
    toast.add({
      severity: 'warn',
      summary: 'Missing Fields',
      detail: 'Please fill in all the fields',
      life: 3000
    });
    return;
  }

  try {
    await axios.post(`${API_URL}/companies/${editCompany.value.id}`, editCompany.value, authHeaders());
    toast.add({ severity: 'success', summary: 'Updated', detail: 'User updated successfully', life: 3000 });
    showEditDialog.value = false;
    await fetchCompanies();
  } catch (err) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: err.response?.data?.detail || 'Failed to update user',
      life: 3000
    });
  }
};

onMounted(fetchCompanies);
</script>

<style scoped>
.field {
  margin-bottom: 1rem;
}
</style>
