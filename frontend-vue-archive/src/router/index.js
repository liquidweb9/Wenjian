import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import ResumeUpload from '../views/ResumeUpload.vue'
import ResumeDetail from '../views/ResumeDetail.vue'
import Interview from '../views/Interview.vue'
import Report from '../views/Report.vue'

const routes = [
  { path: '/', name: 'home', component: Home },
  { path: '/upload', name: 'upload', component: ResumeUpload },
  { path: '/resumes/:id', name: 'resume', component: ResumeDetail },
  { path: '/interview/:id', name: 'interview', component: Interview },
  { path: '/report/:id', name: 'report', component: Report },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
