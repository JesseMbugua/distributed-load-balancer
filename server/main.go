package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
)

type HomeResponse struct {
	Message string `json:"message"`
	Status  string `json:"status"`
}

func homeHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	serverID := os.Getenv("SERVER_ID")
	if serverID == "" {
		serverID = "unknown"
	}

	resp := HomeResponse{
		Message: fmt.Sprintf("Hello from Server: %s", serverID),
		Status:  "successful",
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	if err := json.NewEncoder(w).Encode(resp); err != nil {
		log.Printf("Error encoding response: %v", err)
	}
}

func heartbeatHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	w.WriteHeader(http.StatusOK)
}

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("/home", homeHandler)
	mux.HandleFunc("/heartbeat", heartbeatHandler)

	port := ":5000"
	log.Printf("Server listening on port %s", port)
	if err := http.ListenAndServe(port, mux); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}
