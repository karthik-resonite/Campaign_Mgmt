<script setup>
import { ref } from 'vue';
import { changePassword } from '@/service/authService';

const username = ref('');
const oldpassword = ref('');
const newpassword = ref('');
const errorMessage = ref('');
const successMessage = ref('');

const handleSubmit = async (e) => {
  e.preventDefault();
  errorMessage.value = '';
  successMessage.value = '';

  if (!username.value || !oldpassword.value || !newpassword.value) {
    errorMessage.value = "All fields are required";
    return;
  }

  if (oldpassword.value === newpassword.value) {
    errorMessage.value = "You can't reuse your old password";
    return;
  }

  const token = localStorage.getItem("token");

  try {
    const res = await changePassword(username.value, oldpassword.value, newpassword.value, token);
    successMessage.value = res.data.message;
    // ✅ Clear inputs after success
    username.value = '';
    oldpassword.value = '';
    newpassword.value = '';
  } catch (err) {
    errorMessage.value = err.response?.data?.detail || "Something went wrong";
  }
};
</script>

<template>
  <div class="p-6 max-w-3xl mx-auto">
    <div class="card flex flex-col gap-6">
      <h2 class="text-2xl font-semibold">Change Password</h2>

      <!-- Username -->
      <div class="flex flex-col gap-2">
        <label for="username">Username</label>
        <InputText v-model="username" type="text" placeholder="Enter your username" />
      </div>

      <!-- Old Password -->
      <div class="flex flex-col gap-2">
        <label for="oldpassword">Old Password</label>
        <InputText v-model="oldpassword" type="password" placeholder="Enter your old password" />
      </div>

      <!-- New Password -->
      <div class="flex flex-col gap-2">
        <label for="newpassword">New Password</label>
        <InputText v-model="newpassword" type="password" placeholder="Enter your new password" />
      </div>

      <!-- Submit -->
      <div class="flex justify-end">
        <Button label="Submit" icon="pi pi-check" @click="handleSubmit" />
      </div>

      <!-- Messages -->
      <p v-if="errorMessage" class="text-red-500">{{ errorMessage }}</p>
      <p v-if="successMessage" class="text-green-500">{{ successMessage }}</p>
    </div>
  </div>
</template>