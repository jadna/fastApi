import os
import time
import psutil
import GPUtil
import pandas as pd
import csv
import json
from tabulate import tabulate
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

description = """
UBIQ . 🚀

## Benchmark

You will be able to:

* **Benchmark Server** (Get the data about the NVIDIA GPU from the Ubiq server).
* **Benchmark Client** (Get the data from the client's notebook).
"""

app = FastAPI(
    title="UBIQ",
    description=description,
    version="0.0.1",
    terms_of_service="http://ubiq.com/terms/",
    contact={
        "name": "Ubiq",
        "url": "http://ubiq.hp.com/contact/",
        "email": "ubiq@hp.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },)

csv_file = './server_metrics.csv'

def get_size(bytes, suffix="B"):
    """
    Scale bytes to its proper format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor

csv_file = './server_metrics.csv'

def collecting_data():

    if os.path.exists(csv_file):
        metrics = pd.read_csv(csv_file)
    else:
        metrics = pd.DataFrame()


    print(f'[{datetime.today()}] Starting logger...')

    while True:
        
        gpus = GPUtil.getGPUs()
        svmem = psutil.virtual_memory()
        list_gpus = []
        for gpu in gpus:
            # get the GPU id
            gpu_id = gpu.id
            # name of GPU
            gpu_name = gpu.name
            # get % percentage of GPU usage of that GPU
            gpu_usage = f"{gpu.load*100}%"
            # get free memory in MB format
            gpu_free_memory = f"{gpu.memoryFree}MB"
            # get used memory
            gpu_used_memory = f"{gpu.memoryUsed}MB"
            # get total memory
            gpu_total_memory = f"{gpu.memoryTotal}MB"
            # get GPU temperature in Celsius
            gpu_temperature = f"{gpu.temperature} °C"
            gpu_uuid = gpu.uuid
            # get cpu 
            cpu_usage = f"{psutil.cpu_percent()}%"
            # get ram usage
            ram_total = f"{get_size(svmem.total)}"
            ram_available = f"{get_size(svmem.available)}"
            ram_used = f"{get_size(svmem.used)}"
            ram_usage = f"{svmem.percent}%"

            # datetime
            today = f"{datetime.today()}"

            list_gpus.append((
                gpu_id, gpu_name, gpu_usage, gpu_free_memory, gpu_used_memory, gpu_total_memory, gpu_temperature, gpu_uuid, 
                cpu_usage, ram_total,ram_available, ram_used, ram_usage, today
            ))

        metrics = metrics.append(
            {
                'gpu_id': gpu_id,
                'gpu_name': gpu_name,
                'gpu_usage': gpu_usage,
                'gpu_free_memory': gpu_free_memory,
                'gpu_used_memory': gpu_used_memory,
                'gpu_total_memory': gpu_total_memory,
                'gpu_temperature': gpu_temperature,
                'gpu_uuid': gpu_uuid,
                'cpu_usage': cpu_usage,
                'ram_total': ram_total,
                'ram_available': ram_available, 
                'ram_used': ram_used,
                'memory_usage': ram_usage,
                'datetime': today
            },
            ignore_index=True
        )
        print(tabulate(
            list_gpus, headers=("gpu id", "gpu name", "gpu usage", "gpu free memory", "gpu used memory", "gpu total memory", "gpu temperature", "gpu uuid", 
            "server cpu", 'ram_total', 'ram_available', 'ram_used', 'ram_usage', "date")))


        if not metrics.empty:
            # Convert the date to datetime64 and delete old rows in dataframe
            metrics['datetime'] = pd.to_datetime(metrics['datetime'])
            metrics.drop(metrics[metrics.datetime < (datetime.today() + timedelta(hours=-3))].index, inplace=True)

        metrics.to_csv(csv_file, index=False)

        #print(f"[{today}] Server metrics saved at '{csv_file}'.")
        
        time.sleep(30)
        

@app.get("/")
def index():
    return {"Hello": "World"}



responses = {
    200: {
        "description": "Benchmark of a server GPU NVIDIA.",
        "content" : {
            "text/csv" : {
                "example" : "No example available."
            }
        }
    },
    500: {
        "description": "500 Internal Server Error.",
        "content" : {
            "text/csv" : {
                "example" : "No example available."
            }
        }
    }
}
@app.get("/benchmark", responses=responses)
def benchmark_server():

    metrics = pd.read_csv('server_metrics.csv')
    result = metrics.to_json(orient='records', lines=True)

    json_compatible_item_data = jsonable_encoder(result)
    return JSONResponse(content=json_compatible_item_data)

    #return {result}


if __name__ == "__main__":
    
    collecting_data()
    uvicorn.run(app, host='127.0.0.1', port=8000, debug=True)