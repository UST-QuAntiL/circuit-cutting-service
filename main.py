from planqk.commons.runtime import FileReader, ResponseHandler

from app import wire_cutter
from app.model.request_combine_results import CombineResultsRequest
from app.model.request_cut_circuits import CutCircuitsRequest

if __name__ == "__main__":  # prevent recursive spawning of processes

    with FileReader(["/var/input/data.json", "./input/data.json"]) as f:
        input_data = f.read_to_dict()

    with FileReader(["/var/input/params.json", "./input/params.json"]) as f:
        input_params = f.read_to_dict()

    if not input_data:
        print("Error: data.json file not found")
        exit(1)

    if not input_params:
        print("Error: params.json file not found")
        exit(1)

    if input_params["function"] == "cut":
        result = wire_cutter.cut_circuit(CutCircuitsRequest(**input_data)).to_dict()
    elif input_params["function"] == "combine":
        result = wire_cutter.reconstruct_result(
            CombineResultsRequest(**input_data), input_params["quokka_format"]
        ).to_dict()
    else:
        print(f'Error: Unkown or unspecified function: {input_params["function"]}')
        exit(1)

    # handle the result
    response = ResponseHandler(result)
    response.print_json()
