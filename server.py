from mcp.server.fastmcp import FastMCP
from muna import Acceleration, Dtype, Muna, Predictor
import numpy as np
from PIL import Image
from pydantic import BaseModel, Field
from tempfile import NamedTemporaryFile
from typing import Literal

class MCPScalarValue(BaseModel):
    """
    Scalar value.
    """
    kind: Literal["scalar"] = "scalar"
    data: float | int | bool | str | list[object] | dict[str, object] = Field(description="Scalar value.")

class MCPTensorValue(BaseModel):
    """
    Tensor value.
    """
    kind: Literal["tensor"] = "tensor"
    data: str = Field(description="Path to raw tensor data.")
    dtype: Dtype = Field(description="Tensor data type.")
    shape: list[int] = Field(description="Tensor shape.")

class MCPImageValue(BaseModel): # Mirrors MCP's own `Image` type
    """
    Image value.
    """
    kind: Literal["image"] = "image"
    data: str = Field(description="Path to image file.")

# MCP-compatible prediction value
MCPValue = (
    MCPScalarValue      |
    MCPTensorValue      |
    MCPImageValue
)

class MCPPrediction(BaseModel):
    """
    MCP-compatible prediction.
    """
    id: str = Field(description="Prediction identifier.")
    tag: str = Field(description="Prediction tag.")
    results: list[MCPValue] | None = Field(description="Prediction results.")
    latency: float = Field(description="Prediction latency in milliseconds.")
    error: str | None = Field(description="Prediction error. This is `None` if the prediction completed successfully.")
    logs: str | None = Field(description="Prediction logs.")
    created: str = Field(description="Date created.")

# Create an MCP server
mcp = FastMCP("Levels AI")
# Create a Muna client
muna = Muna()

@mcp.tool(
    title="Search Predictors",
    description=f"""
    Search for prediction functions that solve a given task.

    These predictors are stateless functions which accept data of common types (scalars, tensors, images, etc.).
    The prediction function will provide its detailed signature, including arguments it accepts, 
    schemas for aforementioend argumnts, and output types and schemas.
    """.strip(),
    structured_output=True
)
def search_predictors(query: str) -> list[Predictor]:
    """
    Search for prediction functions that solve a given task.
    """
    SEARCHABLE_TAGS = [ # Until we have some swanky vector search solution (or Algolia perhaps)
        "@fxn/greeting",
        "@cuhk/modnet",
        "@natml/movenet-multipose",
        "@pytorch/resnet-50",
        "@yusuf/yolo-v8-nano",
    ]
    predictors = [muna.predictors.retrieve(tag) for tag in SEARCHABLE_TAGS]
    return predictors

@mcp.tool(
    title="Create a Prediction",
    description=f"""
    Create a prediction.

    This tool can be used to invoke a prediction function, given its tag along with an input value map.
    The prediction function can be invoked locally with varying kinds of hardware acceleration (`auto`, `cpu`, `gpu`, `npu`).
    The prediction function can also be invoked on remote servers (`remote_auto`).
    """.strip(),
    structured_output=True
)
def create_prediction(
    tag: str,
    inputs: dict[str, MCPValue],
    acceleration: Acceleration | Literal["remote_auto"]="auto"
) -> MCPPrediction:
    """
    Make a prediction with a prediction function.
    """
    create_fn = (
        muna.beta.predictions.remote.create
        if acceleration.startswith("remote_")
        else muna.predictions.create
    )
    prediction = create_fn(
        tag=tag,
        inputs={ name: _to_plain_value(value) for name, value in inputs.items() },
        acceleration=acceleration
    )
    return MCPPrediction(
        id=prediction.id,
        tag=prediction.tag,
        results=prediction.results and list(map(_to_mcp_value, prediction.results)),
        latency=prediction.latency,
        error=prediction.error,
        logs=prediction.logs,
        created=prediction.created
    )

def _to_plain_value(value: MCPValue) -> object:
    """
    Deserialize an MCP value to a plain Python value.
    """
    match value.kind:
        case "scalar":  return value.data
        #case "tensor":  return np.frombuffer(b64decode(value.data), dtype=value.dtype).reshape(value.shape)
        case "image":   return Image.open(value.data)
        case _: raise ValueError(f"Cannot deserialize value of type {value.kind} to plain value")

def _to_mcp_value(value: object) -> MCPValue:
    """
    Serialize a value to an MCP-compatible value.
    """
    match value:
        case float():       return MCPScalarValue(data=value)
        case int():         return MCPScalarValue(data=value)
        case bool():        return MCPScalarValue(data=value)
        case str():         return MCPScalarValue(data=value)
        case list():        return MCPScalarValue(data=value)
        case dict():        return MCPScalarValue(data=value)
        # case np.ndarray():
        #     return MCPTensorValue(
        #         data=b64encode(value.tobytes()),
        #         dtype=str(value.dtype),
        #         shape=value.shape
        #     )
        case Image.Image():
            with NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                value.save(temp_file.name, format="png")
                return MCPImageValue(data=temp_file.name)
        case _: raise ValueError(f"Cannot serialize value of type {type(value)} to MCP value")

if __name__ == "__main__":
    mcp.run(transport="stdio")
    #mcp.run(transport="sse")