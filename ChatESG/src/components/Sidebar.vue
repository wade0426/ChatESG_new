<template>
    <div class="sidebar-overlay" v-if="isOpen" @click="handleClose"></div>
    <div class="sidebar" :class="{ 'open': isOpen }">
        <a href="javascript:void(0)" class="close-btn" @click="handleClose">&times;</a>
        <div class="sidebar-content">
            <a href="/home" class="sidebar-item">首頁</a>
            <a href="#" class="sidebar-item">我的設計</a>
            <a href="#" class="sidebar-item">模板庫</a>
            <a href="#" class="sidebar-item">設定</a>
        </div>
    </div>
</template>

<script setup>
const props = defineProps({
    isOpen: {
        type: Boolean,
        default: false
    }
})

const emit = defineEmits(['close'])

const handleClose = () => {
    emit('close')
}
</script>

<style scoped>
.sidebar-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: 150;
}

.sidebar {
    height: 100%;
    width: 0;
    position: fixed;
    z-index: 200;
    top: 0;
    left: 0;
    background-color: #242526;
    overflow-x: hidden;
    transition: all 0.3s ease-in-out;
    padding-top: 60px;
}

.sidebar.open {
    width: 250px;
}

.sidebar-content {
    opacity: 0;
    transition: opacity 0.2s ease-in-out;
}

.sidebar.open .sidebar-content {
    opacity: 1;
}

.sidebar a {
    padding: 8px 8px 8px 32px;
    text-decoration: none;
    font-size: 25px;
    color: #818181;
    display: block;
    transition: 0.3s;
    white-space: nowrap;
}

.sidebar a:hover {
    color: #f1f1f1;
}

.sidebar .close-btn {
    position: absolute;
    top: 0;
    right: 25px;
    font-size: 36px;
    margin-left: 50px;
}
</style> 