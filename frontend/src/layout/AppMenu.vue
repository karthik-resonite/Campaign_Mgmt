<script setup>
import { ref, onMounted, computed } from 'vue';
import AppMenuItem from './AppMenuItem.vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const role = ref(null);

// Get role from localStorage when component is mounted
onMounted(() => {
    role.value = localStorage.getItem("role");
});

// Logout function
const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    localStorage.removeItem("company_id");
    router.replace("/"); // Redirect to login
};

// Menu model based on role
const model = computed(() => {
    const commonItems = [
        //{
           // label: 'Change password',
           // icon: 'pi pi-fw pi-cog',
           // to: '/change_password'
        //},
       // {
           // label: 'Log out',
           // icon: 'pi pi-fw pi-power-off',
           // command: () => logout()
        //}
    ];

    if (role.value === 'admin') {
        return [
            {
                label: '',
                icon: '',
                items: [
                    {
                        label: 'Dashboard',
                        icon: 'pi pi-fw pi-home',
                        to: 'finearc/campaign'
                    },
		    {
                        label: 'User',
                        icon: 'pi pi-fw pi-user',
                        to: '/finearc/user'
                    },
                    {
                        label: 'Campaign List',
                        icon: 'pi pi-fw pi-list',
                        to: '/finearc/campaign_list'
                    },
                    ...commonItems
                ]
            }
        ];
    } else if (role.value === 'user') {
        return [
            {
                label: '',
                icon: '',
                items: [
                    {
                        label: 'Dashboard',
                        icon: 'pi pi-fw pi-home',
                        to: '/finearc/dashboard'
                    },
		    {
                        label: 'Add Customer Data',
                        icon: 'pi pi-fw pi-user',
                        to: '/finearc/customer_data'
                    },
                    {
                        label: 'Campaign List',
                        icon: 'pi pi-fw pi-list',
                        to: '/finearc/campaign_list'
                    },
                    ...commonItems
                ]
            }
        ];
    } else {
        // Default menu or nothing
        return [];
    }
});
</script>

<template>
    <ul class="layout-menu">
        <template v-for="(item, i) in model" :key="i">
            <AppMenuItem v-if="!item.separator" :item="item" root :index="i" />
            <li v-else class="menu-separator" />
        </template>
    </ul>
</template>
