<script setup>
import LazyImage from '@/components/landing/LazyImage.vue';
import Logo from '@/components/landing/Logo.vue';
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { RegistorUser } from "../../service/authService";
import Apple from '../../components/auth/Apple.vue';
import Google from '../../components/auth/Google.vue';

const c_name = ref('');
const username = ref('');
const email = ref('');
const phone = ref('');
const password = ref('');
const remember = ref(false);
const error = ref("");

const router = useRouter();

const register = async (e) => {
  e.preventDefault();
  try {
    const res = await RegistorUser(c_name.value, username.value, email.value, phone.value, password.value);
    const response = res;
    console.log('response', response);
    router.replace("/");
  } catch (err) {
    error.value = err.detail || "Invalid username or password";
  }
};
// function navigateToVerification() {
//     router.push({ path: '/auth/verification' });
// }
</script>
<template>
    <section class="min-h-screen flex items-center lg:items-start lg:py-20 justify-center animate-fadein animate-duration-300 animate-ease-in max-w-[100rem] mx-auto">
        <div class="flex w-full h-full justify-center gap-12">
            <div class="flex flex-col py-5 lg:min-w-[30rem]">
                <!-- <router-link to="/" class="flex items-center justify-center lg:justify-start mb-8">
                    <Logo />
                </router-link> -->
                <div class="flex flex-col justify-center flex-grow">
                    <div class="max-w-md mx-auto w-full">
                        <h5 class="title-h5 text-center lg:text-left">Register</h5>
                        <p class="body-small mt-3.5 text-center lg:text-left">Let's get started</p>
                        <!-- <button class="button-button mt-8"><Google /> Register with Google</button>
                        <button class="button-button mt-4"><Apple /> Register with Apple</button>
                        <div class="flex items-center gap-3.5 my-7">
                            <span class="flex-1 h-[1px] bg-surface-200 dark:bg-surface-800" />
                            <span class="body-small text-surface-400 dark:text-surface-600">or</span>
                            <span class="flex-1 h-[1px] bg-surface-200 dark:bg-surface-800" />
                        </div> -->
                        <InputText type="text" v-model="c_name" class="w-full mt-8" placeholder="Company Name" />
                        <InputText type="text" v-model="username" class="w-full mt-4" placeholder="Username" />
                        <InputText type="text" v-model="email" class="w-full mt-4" placeholder="Email" />
                        <InputText type="number" v-model="phone" class="w-full mt-4" placeholder="Phone Number" />
                        <InputText type="password" v-model="password" class="w-full mt-4" placeholder="Password" />
                        <div class="my-4 flex items-center justify-between">
                            <div class="flex items-center gap-2">
                                <Checkbox inputId="remember" v-model="remember" :binary="true" />
                                <label for="remember" class="body-small"> <span class="label-small text-surface-950 dark:text-surface-0">I have read the </span>Terms and Conditions </label>
                            </div>
                        </div>
                        <button @click="register" type="button" class="body-button w-full">Register</button>
                        <div class="mt-8 body-small text-center lg:text-left">Already have an account? <router-link to="/" class="text-primary-500 hover:underline"> Login</router-link></div>
                    </div>
                </div>
                <!-- <div class="mt-8 text-center lg:text-start block relative text-surface-400 dark:text-surface-500 text-sm">©{{ new Date().getFullYear() }} PrimeTek</div> -->
            </div>
            <div class="hidden lg:flex h-full py-14">
                <div class="h-full w-full lg:max-w-[32.5rem] xl:max-w-[60.5rem] mx-auto flex items-center justify-center shadow-[0px_1px_2px_0px_rgba(18,18,23,0.05)] rounded-3xl border border-surface overflow-hidden">
                    <LazyImage class="w-auto h-full object-contain object-left" src="/demo/images/landing/auth-login.jpg" alt="Auth Image" />
                </div>
            </div>
        </div>
    </section>
</template>