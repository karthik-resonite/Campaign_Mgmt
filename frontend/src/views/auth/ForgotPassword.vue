<script setup>
import Logo from '@/components/landing/Logo.vue';
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { forgotPassword } from "../../service/authService";

const username = ref('');
const error = ref("");

const router = useRouter();

const forgot_password = async (e) => {
  e.preventDefault();
  try {
    const res = await forgotPassword(username.value);
    const response = res;
    console.log('response', response);
    localStorage.setItem("email", res.data.email);
    router.replace("/verification");
  } catch (err) {
    error.value = err.detail || "Invalid username";
  }
};

</script>
<template>
    <section class="min-h-screen flex items-center lg:items-start lg:py-20 justify-center animate-fadein animate-duration-300 animate-ease-in max-w-[100rem] mx-auto">
        <div class="flex w-full h-full justify-center gap-12">
            <div class="flex flex-col py-20 lg:min-w-[30rem]">
                <!-- <router-link to="/" class="flex items-center justify-center lg:justify-start mb-8">
                    <Logo />
                </router-link> -->
                <div class="flex flex-col justify-center flex-grow">
                    <div class="max-w-md mx-auto w-full">
                        <h5 class="title-h5 text-center lg:text-left">Forgot Password</h5>
                        <p class="body-small mt-3.5 text-center lg:text-left">Enter your Username to reset your password</p>
                        <form>
                            <InputText type="text" v-model="username" class="w-full mt-7" placeholder="Username" />
                            <div class="flex items-center gap-4 mt-8">
                                <router-link to="/" class="body-button border border-surface-200 dark:border-surface-800 bg-transparent hover:bg-surface-100 dark:hover:bg-surface-800 text-surface-950 dark:text-surface-0 flex-1">Cancel</router-link>
                                <button type="submit" class="body-button flex-1" @click="forgot_password">Submit</button>
                            </div>
                        </form>
                        <div class="mt-8 body-small text-center lg:text-left">A problem? <a class="underline cursor-pointer hover:opacity-75 transition-all">Click here</a> and let us help you.</div>
                    </div>
                </div>
                <!-- <div class="mt-8 text-center lg:text-start block relative text-surface-400 dark:text-surface-500 text-sm">©{{ new Date().getFullYear() }} PrimeTek</div> -->
            </div>
            <div class="hidden lg:flex h-full py-20">
                <div class="h-full w-full lg:max-w-[32.5rem] xl:max-w-[60.5rem] mx-auto flex items-center justify-center shadow-[0px_1px_2px_0px_rgba(18,18,23,0.05)] rounded-3xl border border-surface overflow-hidden">
                    <LazyImage class="w-auto h-full object-contain object-left" src="/demo/images/landing/auth-login.jpg" alt="Auth Image" />
                </div>
            </div>
        </div>
    </section>
</template>
