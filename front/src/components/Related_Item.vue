<template>
    <div class="container my-5">
        <h1 class="text-center mb-4">Recommendation</h1>
        <div class="card p-4 mb-4">
            <form @submit.prevent>
                <div class="mb-3">
                    <input type="text" class="form-control bg-light" v-model="input_object" placeholder="解決したい課題を入力してください" />
                </div>
                <button @click="Related_Items" class="btn btn-primary w-100 mt-3">search</button>
                <button @click="Roald_Graph"  class="btn btn-primary w-100 mt-3">Graph</button>
            </form>
        </div>

        <div v-if="isLoading" class="d-flex justify-content-center">
            <div  class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>

        <div class="row">
            <div class="col-md-12 mb-4">
                <div class="card" v-if="items" style="background-color: #f0f8ff;">
                    <div class="card-body">
                        <h2 class="card-title text-center mb-4">Results</h2>
                        <div class="card mb-3">
                            <div class="card-body">
                                <h5 class="card-title border-bottom pb-2">Methods</h5>
                                <p class="card-text">{{ items.method }}</p>
                            </div>
                        </div>
                        <div class="card mb-3">
                            <div class="card-body">
                                <h5 class="card-title border-bottom pb-2">Datasets</h5>
                                <p class="card-text">{{ items.dataset }}</p>
                            </div>
                        </div> 
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-12 mb-4">
                <div class="card" v-if="graphUrl" style="background-color: #f0f8ff;">
                    <div class="card-body">
                        <h2 class="card-title text-center mb-4">Graph</h2>
                        <div class="card mb-3">
                            <iframe
                            :src="graphUrl"
                            frameborder="0"
                            :style="{ 
                                width: '100%', 
                                height: '600px', 
                                border: '1px solid #ccc', 
                                borderRadius: '10px', 
                                boxShadow: '0px 4px 6px rgba(0, 0, 0, 0.1)' 
                            }" 
                            ></iframe>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div v-if="error">
            <p>{{ error }}</p>
        </div>
    </div>
</template>

<script>
import axios from "axios";

export default {
  data() {
      return {
        input_object: "",
        items: null,
        graphUrl: "",
        isLoading: false,
        showGraph: false,
        error: null
      };
  },
  methods: {
      async Related_Items() {
        this.error = null;
        this.isLoading = true;
        try {
            const payload = {
                input_object: this.input_object
            };
            const response = await axios.post("http://127.0.0.1:8000/items/", payload);
            if (response.data.error_message) {
                throw new Error(response.data.error_message);
            }
            this.items = response.data;
        } catch (err) {
            this.error = err.message;
        } finally {
            this.isLoading = false;
        }
      },
      async Roald_Graph() {
        this.error = null;
        this.isLoading = true;
        try {
            const payload = {
                input_object: this.input_object
            };
            const response = await axios.post("http://127.0.0.1:8000/graph/", payload, {
                responseType: "blob",
            });
            const blob = new Blob([response.data], {type: "text/html"});
            this.graphUrl = URL.createObjectURL(blob);
            this.showGraph = true;
        } catch (err) {
            this.error = err.message;
        } finally {
            this.isLoading = false;
        }
      },
  },
};
</script>


<style scoped>

</style>