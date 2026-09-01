import json
import matplotlib.pyplot as plt

def plot_a1():
    try:
        with open("a1_results.json", "r") as f:
            data = json.load(f)
        
        servers = list(data.keys())
        counts = list(data.values())

        plt.figure(figsize=(8, 5))
        plt.bar(servers, counts, color='royalblue', edgecolor='black')
        plt.title("A-1: Request Distribution on N=3 Servers (10,000 Requests)")
        plt.xlabel("Server Instance")
        plt.ylabel("Request Count")
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig("a1_distribution.png")
        plt.close()
        print("Generated a1_distribution.png")
    except Exception as e:
        print(f"Could not plot A-1: {e}")

def plot_a2():
    try:
        with open("a2_results.json", "r") as f:
            data = json.load(f)
        
        n_values = [int(k) for k in data.keys()]
        avg_loads = [data[k]["average_load"] for k in data.keys()]

        plt.figure(figsize=(8, 5))
        plt.plot(n_values, avg_loads, marker='o', color='darkorange', linewidth=2)
        plt.title("A-2: Scalability - Average Load per Server vs Number of Servers (N)")
        plt.xlabel("Number of Server Containers (N)")
        plt.ylabel("Average Requests per Server")
        plt.xticks(n_values)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig("a2_scalability.png")
        plt.close()
        print("Generated a2_scalability.png")
    except Exception as e:
        print(f"Could not plot A-2: {e}")

if __name__ == '__main__':
    plot_a1()
    plot_a2()