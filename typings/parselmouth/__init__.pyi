import numpy
import tgt.core
import typing
from . import praat as praat
from typing import ClassVar, Iterator, TypeVar, Generic, Any
from numpy.typing import NDArray

_T = TypeVar("_T")
class Positive(Generic[_T]): ...
class NonNegative(Generic[_T]): ...

PRAAT_VERSION: str
PRAAT_VERSION_DATE: str
VERSION: str
__version__: str

class AmplitudeScaling:
    __members__: ClassVar[dict] = ...  # read-only
    INTEGRAL: ClassVar[AmplitudeScaling] = ...
    NORMALIZE: ClassVar[AmplitudeScaling] = ...
    PEAK_0_99: ClassVar[AmplitudeScaling] = ...
    SUM: ClassVar[AmplitudeScaling] = ...
    __entries: ClassVar[dict] = ...
    def __init__(self, *args, **kwargs) -> None:
        """__init__(self: parselmouth.AmplitudeScaling, value: int) -> None \\\n        __init__(self: parselmouth.AmplitudeScaling, arg0: str) -> None
        """
    def __eq__(self, other: object) -> bool:
        """__eq__(self: object, other: object) -> bool"""
    def __hash__(self) -> int:
        """__hash__(self: object) -> int"""
    def __index__(self) -> int:
        """__index__(self: parselmouth.AmplitudeScaling) -> int"""
    def __int__(self) -> int:
        """__int__(self: parselmouth.AmplitudeScaling) -> int"""
    def __ne__(self, other: object) -> bool:
        """__ne__(self: object, other: object) -> bool"""
    @property
    def name(self) -> str:
        """name(self: handle) -> str

        name(self: handle) -> str
        """
    @property
    def value(self) -> int:
        """(arg0: parselmouth.AmplitudeScaling) -> int"""

class CC(TimeFrameSampled):
    class Frame:
        c0: float
        def __init__(self, *args, **kwargs) -> None:
            """Initialize self.  See help(type(self)) for accurate signature."""
        def to_array(self) -> NDArray[numpy.float64]:
            """to_array(self: parselmouth.CC.Frame) -> NDArray[numpy.float64]"""
        def __getitem__(self, i: int) -> float:
            """__getitem__(self: parselmouth.CC.Frame, i: int) -> float"""
        def __iter__(self) -> typing.Iterator[float]:
            """def __iter__(self) -> typing.Iterator[float]"""
        def __len__(self) -> int:
            """__len__(self: parselmouth.CC.Frame) -> int"""
        def __setitem__(self, i: int, value: float) -> None:
            """__setitem__(self: parselmouth.CC.Frame, i: int, value: float) -> None"""
        @property
        def c(self) -> numpy.ndarray:
            """(arg0: parselmouth.CC.Frame) -> numpy.ndarray"""
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def get_c0_value_in_frame(self, frame_number: Positive[int]) -> float:
        """get_c0_value_in_frame(self: parselmouth.CC, frame_number: Positive[int]) -> float"""
    def get_frame(self, frame_number: Positive[int]) -> CC.Frame:
        """get_frame(self: parselmouth.CC, frame_number: Positive[int]) -> parselmouth.CC.Frame"""
    def get_number_of_coefficients(self, frame_number: Positive[int]) -> int:
        """get_number_of_coefficients(self: parselmouth.CC, frame_number: Positive[int]) -> int"""
    def get_value_in_frame(self, frame_number: Positive[int], index: Positive[int]) -> float:
        """get_value_in_frame(self: parselmouth.CC, frame_number: Positive[int], index: Positive[int]) -> float"""
    def to_array(self) -> NDArray[numpy.float64]:
        """to_array(self: parselmouth.CC) -> NDArray[numpy.float64]"""
    def to_matrix(self) -> Matrix:
        """to_matrix(self: parselmouth.CC) -> parselmouth.Matrix"""
    def __getitem__(self, index):
        """__getitem__(self: parselmouth.CC, i: int) -> parselmouth.CC.Frame \\\n        __getitem__(self: parselmouth.CC, ij: Tuple[int, int]) -> float
        """
    def __iter__(self) -> Iterator:
        """__iter__(self: parselmouth.CC) -> Iterator"""
    def __setitem__(self, ij: tuple[int, int], value: float) -> None:
        """__setitem__(self: parselmouth.CC, ij: Tuple[int, int], value: float) -> None"""
    @property
    def fmax(self) -> float:
        """(self: parselmouth.CC) -> float"""
    @property
    def fmin(self) -> float:
        """(self: parselmouth.CC) -> float"""
    @property
    def max_n_coefficients(self) -> int:
        """(self: parselmouth.CC) -> int"""

class Data(Thing):
    class FileFormat:
        __members__: ClassVar[dict] = ...  # read-only
        BINARY: ClassVar[Data.FileFormat] = ...
        SHORT_TEXT: ClassVar[Data.FileFormat] = ...
        TEXT: ClassVar[Data.FileFormat] = ...
        __entries: ClassVar[dict] = ...
        def __init__(self, *args, **kwargs) -> None:
            """__init__(self: parselmouth.Data.FileFormat, value: int) -> None \\\n            __init__(self: parselmouth.Data.FileFormat, arg0: str) -> None
            """
        def __eq__(self, other: object) -> bool:
            """__eq__(self: object, other: object) -> bool"""
        def __hash__(self) -> int:
            """__hash__(self: object) -> int"""
        def __index__(self) -> int:
            """__index__(self: parselmouth.Data.FileFormat) -> int"""
        def __int__(self) -> int:
            """__int__(self: parselmouth.Data.FileFormat) -> int"""
        def __ne__(self, other: object) -> bool:
            """__ne__(self: object, other: object) -> bool"""
        @property
        def name(self) -> str:
            """name(self: handle) -> str

            name(self: handle) -> str
            """
        @property
        def value(self) -> int:
            """(arg0: parselmouth.Data.FileFormat) -> int"""
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def copy(self) -> Data:
        """copy(self: parselmouth.Data) -> parselmouth.Data"""
    @staticmethod
    def read(file_path: str) -> Data:
        """read(file_path: str) -> parselmouth.Data

        Read a file into a `parselmouth.Data` object.

        Parameters
        ----------
        file_path : str
            The path of the file on disk to read.

        Returns
        -------
        parselmouth.Data
            The Praat Data object that was read.

        See also
        --------
        :praat:`Read from file...`
        """
    def save(self, file_path: str, format: Data.FileFormat = ...) -> None:
        """save(self: parselmouth.Data, file_path: str, format: parselmouth.Data.FileFormat = <FileFormat.TEXT: 0>) -> None"""
    def save_as_binary_file(self, file_path: str) -> None:
        """save_as_binary_file(self: parselmouth.Data, file_path: str) -> None"""
    def save_as_short_text_file(self, file_path: str) -> None:
        """save_as_short_text_file(self: parselmouth.Data, file_path: str) -> None"""
    def save_as_text_file(self, file_path: str) -> None:
        """save_as_text_file(self: parselmouth.Data, file_path: str) -> None"""
    def __copy__(self) -> Data:
        """__copy__(self: parselmouth.Data) -> parselmouth.Data"""
    def __deepcopy__(self, memo: dict) -> Data:
        """__deepcopy__(self: parselmouth.Data, memo: dict) -> parselmouth.Data"""
    def __eq__(self, other: object) -> bool:
        """__eq__(self: parselmouth.Data, other: object) -> bool"""
    def __ne__(self, other: object) -> bool:
        """__ne__(self: parselmouth.Data, other: object) -> bool"""

class Formant(TimeFrameSampled):
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def get_bandwidth_at_time(self, formant_number: Positive[int], time: float, unit: FormantUnit = ...) -> float:
        """get_bandwidth_at_time(self: parselmouth.Formant, formant_number: Positive[int], time: float, unit: parselmouth.FormantUnit = <FormantUnit.HERTZ: 0>) -> float"""
    def get_value_at_time(self, formant_number: Positive[int], time: float, unit: FormantUnit = ...) -> float:
        """get_value_at_time(self: parselmouth.Formant, formant_number: Positive[int], time: float, unit: parselmouth.FormantUnit = <FormantUnit.HERTZ: 0>) -> float"""

class FormantUnit:
    __members__: ClassVar[dict] = ...  # read-only
    BARK: ClassVar[FormantUnit] = ...
    HERTZ: ClassVar[FormantUnit] = ...
    __entries: ClassVar[dict] = ...
    def __init__(self, *args, **kwargs) -> None:
        """__init__(self: parselmouth.FormantUnit, value: int) -> None \\\n        __init__(self: parselmouth.FormantUnit, arg0: str) -> None
        """
    def __eq__(self, other: object) -> bool:
        """__eq__(self: object, other: object) -> bool"""
    def __hash__(self) -> int:
        """__hash__(self: object) -> int"""
    def __index__(self) -> int:
        """__index__(self: parselmouth.FormantUnit) -> int"""
    def __int__(self) -> int:
        """__int__(self: parselmouth.FormantUnit) -> int"""
    def __ne__(self, other: object) -> bool:
        """__ne__(self: object, other: object) -> bool"""
    @property
    def name(self) -> str:
        """name(self: handle) -> str

        name(self: handle) -> str
        """
    @property
    def value(self) -> int:
        """(arg0: parselmouth.FormantUnit) -> int"""

class Function(Data):
    xmax: float
    xmin: float
    xrange: tuple[float, float]
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def scale_x_by(self, scale: Positive[float]) -> None:
        """scale_x_by(self: parselmouth.Function, scale: Positive[float]) -> None"""
    def scale_x_to(self, new_xmin: float, new_xmax: float) -> None:
        """scale_x_to(self: parselmouth.Function, new_xmin: float, new_xmax: float) -> None"""
    def shift_x_by(self, shift: float) -> None:
        """shift_x_by(self: parselmouth.Function, shift: float) -> None"""
    def shift_x_to(self, x: float, new_x: float) -> None:
        """shift_x_to(self: parselmouth.Function, x: float, new_x: float) -> None"""

class Harmonicity(TimeFrameSampled, Vector):
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def get_value(self, time: float, interpolation: ValueInterpolation = ...) -> float:  # type: ignore[override]
        """get_value(self: parselmouth.Harmonicity, time: float, interpolation: parselmouth.ValueInterpolation = <ValueInterpolation.CUBIC: 2>) -> float"""

class Intensity(TimeFrameSampled, Vector):
    class AveragingMethod:
        __members__: ClassVar[dict] = ...  # read-only
        DB: ClassVar[Intensity.AveragingMethod] = ...
        ENERGY: ClassVar[Intensity.AveragingMethod] = ...
        MEDIAN: ClassVar[Intensity.AveragingMethod] = ...
        SONES: ClassVar[Intensity.AveragingMethod] = ...
        __entries: ClassVar[dict] = ...
        def __init__(self, *args, **kwargs) -> None:
            """__init__(self: parselmouth.Intensity.AveragingMethod, value: int) -> None \\\n            __init__(self: parselmouth.Intensity.AveragingMethod, arg0: str) -> None
            """
        def __eq__(self, other: object) -> bool:
            """__eq__(self: object, other: object) -> bool"""
        def __hash__(self) -> int:
            """__hash__(self: object) -> int"""
        def __index__(self) -> int:
            """__index__(self: parselmouth.Intensity.AveragingMethod) -> int"""
        def __int__(self) -> int:
            """__int__(self: parselmouth.Intensity.AveragingMethod) -> int"""
        def __ne__(self, other: object) -> bool:
            """__ne__(self: object, other: object) -> bool"""
        @property
        def name(self) -> str:
            """name(self: handle) -> str

            name(self: handle) -> str
            """
        @property
        def value(self) -> int:
            """(arg0: parselmouth.Intensity.AveragingMethod) -> int"""
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def get_average(self, from_time: float | None = ..., to_time: float | None = ..., averaging_method: Intensity.AveragingMethod = ...) -> float:
        """get_average(self: parselmouth.Intensity, from_time: Optional[float] = None, to_time: Optional[float] = None, averaging_method: parselmouth.Intensity.AveragingMethod = <AveragingMethod.ENERGY: 1>) -> float"""
    def get_value(self, time: float, interpolation: ValueInterpolation = ...) -> float:  # type: ignore[override]
        """get_value(self: parselmouth.Intensity, time: float, interpolation: parselmouth.ValueInterpolation = <ValueInterpolation.CUBIC: 2>) -> float"""

class Interpolation:
    __members__: ClassVar[dict] = ...  # read-only
    CUBIC: ClassVar[ValueInterpolation] = ...
    LINEAR: ClassVar[ValueInterpolation] = ...
    NEAREST: ClassVar[ValueInterpolation] = ...
    SINC70: ClassVar[ValueInterpolation] = ...
    SINC700: ClassVar[ValueInterpolation] = ...
    __entries: ClassVar[dict] = ...
    def __init__(self, *args, **kwargs) -> None:
        """__init__(self: parselmouth.ValueInterpolation, value: int) -> None \\\n        __init__(self: parselmouth.ValueInterpolation, arg0: str) -> None
        """
    def __eq__(self, other: object) -> bool:
        """__eq__(self: object, other: object) -> bool"""
    def __hash__(self) -> int:
        """__hash__(self: object) -> int"""
    def __index__(self) -> int:
        """__index__(self: parselmouth.ValueInterpolation) -> int"""
    def __int__(self) -> int:
        """__int__(self: parselmouth.ValueInterpolation) -> int"""
    def __ne__(self, other: object) -> bool:
        """__ne__(self: object, other: object) -> bool"""
    @property
    def name(self) -> str:
        """name(self: handle) -> str

        name(self: handle) -> str
        """
    @property
    def value(self) -> int:
        """(arg0: parselmouth.ValueInterpolation) -> int"""

class MFCC(CC):
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def convolve(self, other: MFCC, scaling: AmplitudeScaling = ..., signal_outside_time_domain: SignalOutsideTimeDomain = ...) -> Sound:
        """convolve(self: parselmouth.MFCC, other: parselmouth.MFCC, scaling: parselmouth.AmplitudeScaling = <AmplitudeScaling.PEAK_0_99: 4>, signal_outside_time_domain: parselmouth.SignalOutsideTimeDomain = <SignalOutsideTimeDomain.ZERO: 1>) -> parselmouth.Sound"""
    def cross_correlate(self, other: MFCC, scaling: AmplitudeScaling = ..., signal_outside_time_domain: SignalOutsideTimeDomain = ...) -> Sound:
        """cross_correlate(self: parselmouth.MFCC, other: parselmouth.MFCC, scaling: parselmouth.AmplitudeScaling = <AmplitudeScaling.PEAK_0_99: 4>, signal_outside_time_domain: parselmouth.SignalOutsideTimeDomain = <SignalOutsideTimeDomain.ZERO: 1>) -> parselmouth.Sound"""
    def extract_features(self, window_length: Positive[float] = ..., include_energy: bool = ...) -> Matrix:
        """extract_features(self: parselmouth.MFCC, window_length: Positive[float] = 0.025, include_energy: bool = False) -> parselmouth.Matrix"""
    def to_matrix_features(self, window_length: Positive[float] = ..., include_energy: bool = ...) -> Matrix:
        """to_matrix_features(self: parselmouth.MFCC, window_length: Positive[float] = 0.025, include_energy: bool = False) -> parselmouth.Matrix"""
    def to_sound(self) -> Sound:
        """to_sound(self: parselmouth.MFCC) -> parselmouth.Sound"""

class Matrix(SampledXY):
    values: NDArray[numpy.float64]
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def as_array(self) -> NDArray[numpy.float64]:
        """as_array(self: parselmouth.Matrix) -> NDArray[numpy.float64]"""
    def at_xy(self, x: float, y: float) -> float:
        """at_xy(self: parselmouth.Matrix, x: float, y: float) -> float"""
    def formula(self, *args, **kwargs):
        """formula(self: parselmouth.Matrix, formula: str, from_x: Optional[float] = None, to_x: Optional[float] = None, from_y: Optional[float] = None, to_y: Optional[float] = None) -> None \\\n        formula(self: parselmouth.Matrix, formula: str, x_range: Tuple[Optional[float], Optional[float]] = (None, None), y_range: Tuple[Optional[float], Optional[float]] = (None, None)) -> None
        """
    def get_column_distance(self) -> float:
        """get_column_distance(self: parselmouth.Matrix) -> float"""
    def get_highest_x(self) -> float:
        """get_highest_x(self: parselmouth.Matrix) -> float"""
    def get_highest_y(self) -> float:
        """get_highest_y(self: parselmouth.Matrix) -> float"""
    def get_lowest_x(self) -> float:
        """get_lowest_x(self: parselmouth.Matrix) -> float"""
    def get_lowest_y(self) -> float:
        """get_lowest_y(self: parselmouth.Matrix) -> float"""
    def get_maximum(self) -> float:
        """get_maximum(self: parselmouth.Matrix) -> float"""
    def get_minimum(self) -> float:
        """get_minimum(self: parselmouth.Matrix) -> float"""
    def get_number_of_columns(self) -> int:
        """get_number_of_columns(self: parselmouth.Matrix) -> int"""
    def get_number_of_rows(self) -> int:
        """get_number_of_rows(self: parselmouth.Matrix) -> int"""
    def get_row_distance(self) -> float:
        """get_row_distance(self: parselmouth.Matrix) -> float"""
    def get_sum(self) -> float:
        """get_sum(self: parselmouth.Matrix) -> float"""
    def get_value_at_xy(self, x: float, y: float) -> float:
        """get_value_at_xy(self: parselmouth.Matrix, x: float, y: float) -> float"""
    def get_value_in_cell(self, row_number: Positive[int], column_number: Positive[int]) -> float:
        """get_value_in_cell(self: parselmouth.Matrix, row_number: Positive[int], column_number: Positive[int]) -> float"""
    def get_x_of_column(self, column_number: Positive[int]) -> float:
        """get_x_of_column(self: parselmouth.Matrix, column_number: Positive[int]) -> float"""
    def get_y_of_row(self, row_number: Positive[int]) -> float:
        """get_y_of_row(self: parselmouth.Matrix, row_number: Positive[int]) -> float"""
    def save_as_headerless_spreadsheet_file(self, file_path: str) -> None:
        """save_as_headerless_spreadsheet_file(self: parselmouth.Matrix, file_path: str) -> None"""
    def save_as_matrix_text_file(self, file_path: str) -> None:
        """save_as_matrix_text_file(self: parselmouth.Matrix, file_path: str) -> None"""
    def set_value(self, row_number: Positive[int], column_number: Positive[int], new_value: float) -> None:
        """set_value(self: parselmouth.Matrix, row_number: Positive[int], column_number: Positive[int], new_value: float) -> None"""
    def __buffer__(self, *args, **kwargs):
        """Return a buffer object that exposes the underlying memory of the object."""
    def __release_buffer__(self, *args, **kwargs):
        """Release the buffer object that exposes the underlying memory of the object."""
    @property
    def n_columns(self) -> int:
        """(self: parselmouth.Matrix) -> int"""
    @property
    def n_rows(self) -> int:
        """(self: parselmouth.Matrix) -> int"""

class Pitch(TimeFrameSampled):
    class Candidate:
        def __init__(self, *args, **kwargs) -> None:
            """Initialize self.  See help(type(self)) for accurate signature."""
        @property
        def frequency(self) -> float:
            """(self: parselmouth.Pitch.Candidate) -> float"""
        @property
        def strength(self) -> float:
            """(self: parselmouth.Pitch.Candidate) -> float"""

    class Frame:
        selected: Pitch.Candidate
        def __init__(self, *args, **kwargs) -> None:
            """Initialize self.  See help(type(self)) for accurate signature."""
        def as_array(self) -> numpy.ndarray:
            """as_array(self: parselmouth.Pitch.Frame) -> numpy.ndarray"""
        def select(self, *args, **kwargs):
            """select(self: parselmouth.Pitch.Frame, candidate: parselmouth.Pitch.Candidate) -> None \\\n            select(self: parselmouth.Pitch.Frame, i: int) -> None
            """
        def unvoice(self) -> None:
            """unvoice(self: parselmouth.Pitch.Frame) -> None"""
        def __getitem__(self, i: int) -> Pitch.Candidate:
            """__getitem__(self: parselmouth.Pitch.Frame, i: int) -> parselmouth.Pitch.Candidate"""
        def __iter__(self) -> typing.Iterator[Pitch.Candidate]:
            """def __iter__(self) -> typing.Iterator[Pitch.Candidate]"""
        def __len__(self) -> int:
            """__len__(self: parselmouth.Pitch.Frame) -> int"""
        @property
        def candidates(self) -> list[Pitch.Candidate]:
            """(arg0: parselmouth.Pitch.Frame) -> List[parselmouth.Pitch.Candidate]"""
        @property
        def intensity(self) -> float:
            """(self: parselmouth.Pitch.Frame) -> float"""
    ceiling: float
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def count_differences(self, other: Pitch) -> str:
        """count_differences(self: parselmouth.Pitch, other: parselmouth.Pitch) -> str"""
    def count_voiced_frames(self) -> int:
        """count_voiced_frames(self: parselmouth.Pitch) -> int"""
    def fifth_down(self, from_time: float | None = ..., to_time: float | None = ...) -> None:
        """fifth_down(self: parselmouth.Pitch, from_time: Optional[float] = None, to_time: Optional[float] = None) -> None"""
    def fifth_up(self, from_time: float | None = ..., to_time: float | None = ...) -> None:
        """fifth_up(self: parselmouth.Pitch, from_time: Optional[float] = None, to_time: Optional[float] = None) -> None"""
    def formula(self, formula: str) -> None:
        """formula(self: parselmouth.Pitch, formula: str) -> None"""
    def get_frame(self, frame_number: Positive[int]) -> Pitch.Frame:
        """get_frame(self: parselmouth.Pitch, frame_number: Positive[int]) -> parselmouth.Pitch.Frame"""
    def get_mean_absolute_slope(self, unit: PitchUnit = ...) -> float:
        """get_mean_absolute_slope(self: parselmouth.Pitch, unit: parselmouth.PitchUnit = <PitchUnit.HERTZ: 0>) -> float"""
    def get_slope_without_octave_jumps(self) -> float:
        """get_slope_without_octave_jumps(self: parselmouth.Pitch) -> float"""
    def get_value_at_time(self, time: float, unit: PitchUnit = ..., interpolation: ValueInterpolation = ...) -> float:
        """get_value_at_time(self: parselmouth.Pitch, time: float, unit: parselmouth.PitchUnit = <PitchUnit.HERTZ: 0>, interpolation: parselmouth.ValueInterpolation = <ValueInterpolation.LINEAR: 1>) -> float"""
    def get_value_in_frame(self, frame_number: int, unit: PitchUnit = ...) -> float:
        """get_value_in_frame(self: parselmouth.Pitch, frame_number: int, unit: parselmouth.PitchUnit = <PitchUnit.HERTZ: 0>) -> float"""
    def interpolate(self) -> Pitch:
        """interpolate(self: parselmouth.Pitch) -> parselmouth.Pitch"""
    def kill_octave_jumps(self) -> Pitch:
        """kill_octave_jumps(self: parselmouth.Pitch) -> parselmouth.Pitch"""
    def octave_down(self, from_time: float | None = ..., to_time: float | None = ...) -> None:
        """octave_down(self: parselmouth.Pitch, from_time: Optional[float] = None, to_time: Optional[float] = None) -> None"""
    def octave_up(self, from_time: float | None = ..., to_time: float | None = ...) -> None:
        """octave_up(self: parselmouth.Pitch, from_time: Optional[float] = None, to_time: Optional[float] = None) -> None"""
    def path_finder(self, silence_threshold: float = ..., voicing_threshold: float = ..., octave_cost: float = ..., octave_jump_cost: float = ..., voiced_unvoiced_cost: float = ..., ceiling: Positive[float] = ..., pull_formants: bool = ...) -> None:
        """path_finder(self: parselmouth.Pitch, silence_threshold: float = 0.03, voicing_threshold: float = 0.45, octave_cost: float = 0.01, octave_jump_cost: float = 0.35, voiced_unvoiced_cost: float = 0.14, ceiling: Positive[float] = 600.0, pull_formants: bool = False) -> None"""
    def smooth(self, bandwidth: Positive[float] = ...) -> Pitch:
        """smooth(self: parselmouth.Pitch, bandwidth: Positive[float] = 10.0) -> parselmouth.Pitch"""
    def step(self, step: float, precision: Positive[float] = ..., from_time: float | None = ..., to_time: float | None = ...) -> None:
        """step(self: parselmouth.Pitch, step: float, precision: Positive[float] = 0.1, from_time: Optional[float] = None, to_time: Optional[float] = None) -> None"""
    def subtract_linear_fit(self, unit: PitchUnit = ...) -> Pitch:
        """subtract_linear_fit(self: parselmouth.Pitch, unit: parselmouth.PitchUnit = <PitchUnit.HERTZ: 0>) -> parselmouth.Pitch"""
    def to_array(self) -> NDArray[Any]:
        """to_array(self: parselmouth.Pitch) -> numpy.ndarray[parselmouth.Pitch.Candidate]"""
    def to_matrix(self) -> Matrix:
        """to_matrix(self: parselmouth.Pitch) -> parselmouth.Matrix"""
    def to_sound_hum(self, from_time: float | None = ..., to_time: float | None = ...) -> Sound:
        """to_sound_hum(self: parselmouth.Pitch, from_time: Optional[float] = None, to_time: Optional[float] = None) -> parselmouth.Sound"""
    def to_sound_pulses(self, from_time: float | None = ..., to_time: float | None = ...) -> Sound:
        """to_sound_pulses(self: parselmouth.Pitch, from_time: Optional[float] = None, to_time: Optional[float] = None) -> parselmouth.Sound"""
    def to_sound_sine(self, from_time: float | None = ..., to_time: float | None = ..., sampling_frequency: Positive[float] = ..., round_to_nearest_zero_crossing: float = ...) -> Sound:
        """to_sound_sine(self: parselmouth.Pitch, from_time: Optional[float] = None, to_time: Optional[float] = None, sampling_frequency: Positive[float] = 44100.0, round_to_nearest_zero_crossing: float = True) -> parselmouth.Sound"""
    def unvoice(self, from_time: float | None = ..., to_time: float | None = ...) -> None:
        """unvoice(self: parselmouth.Pitch, from_time: Optional[float] = None, to_time: Optional[float] = None) -> None"""
    def __getitem__(self, index):
        """__getitem__(self: parselmouth.Pitch, i: int) -> parselmouth.Pitch.Frame \\\n        __getitem__(self: parselmouth.Pitch, ij: Tuple[int, int]) -> parselmouth.Pitch.Candidate
        """
    def __iter__(self) -> Iterator:
        """__iter__(self: parselmouth.Pitch) -> Iterator"""
    @property
    def max_n_candidates(self) -> int:
        """(self: parselmouth.Pitch) -> int"""
    @property
    def selected(self) -> list[Pitch.Candidate]:
        """(arg0: parselmouth.Pitch) -> List[parselmouth.Pitch.Candidate]"""
    @property
    def selected_array(self) -> NDArray[Any]:
        """(arg0: parselmouth.Pitch) -> numpy.ndarray[parselmouth.Pitch.Candidate]"""

class PitchUnit:
    __members__: ClassVar[dict] = ...  # read-only
    ERB: ClassVar[PitchUnit] = ...
    HERTZ: ClassVar[PitchUnit] = ...
    HERTZ_LOGARITHMIC: ClassVar[PitchUnit] = ...
    LOG_HERTZ: ClassVar[PitchUnit] = ...
    MEL: ClassVar[PitchUnit] = ...
    SEMITONES_1: ClassVar[PitchUnit] = ...
    SEMITONES_100: ClassVar[PitchUnit] = ...
    SEMITONES_200: ClassVar[PitchUnit] = ...
    SEMITONES_440: ClassVar[PitchUnit] = ...
    __entries: ClassVar[dict] = ...
    def __init__(self, *args, **kwargs) -> None:
        """__init__(self: parselmouth.PitchUnit, value: int) -> None \\\n        __init__(self: parselmouth.PitchUnit, arg0: str) -> None
        """
    def __eq__(self, other: object) -> bool:
        """__eq__(self: object, other: object) -> bool"""
    def __hash__(self) -> int:
        """__hash__(self: object) -> int"""
    def __index__(self) -> int:
        """__index__(self: parselmouth.PitchUnit) -> int"""
    def __int__(self) -> int:
        """__int__(self: parselmouth.PitchUnit) -> int"""
    def __ne__(self, other: object) -> bool:
        """__ne__(self: object, other: object) -> bool"""
    @property
    def name(self) -> str:
        """name(self: handle) -> str

        name(self: handle) -> str
        """
    @property
    def value(self) -> int:
        """(arg0: parselmouth.PitchUnit) -> int"""

class PraatError(RuntimeError): ...

class PraatFatal(BaseException): ...

class PraatWarning(UserWarning): ...

class Sampled(Function):
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def x_bins(self) -> NDArray[numpy.float64]:
        """x_bins(self: parselmouth.Sampled) -> NDArray[numpy.float64]"""
    def x_grid(self) -> NDArray[numpy.float64]:
        """x_grid(self: parselmouth.Sampled) -> NDArray[numpy.float64]"""
    def xs(self) -> NDArray[numpy.float64]:
        """xs(self: parselmouth.Sampled) -> NDArray[numpy.float64]"""
    def __len__(self) -> int:
        """__len__(self: parselmouth.Sampled) -> int"""
    @property
    def dx(self) -> float:
        """(self: parselmouth.Sampled) -> float"""
    @property
    def nx(self) -> int:
        """(self: parselmouth.Sampled) -> int"""
    @property
    def x1(self) -> float:
        """(self: parselmouth.Sampled) -> float"""

class SampledXY(Sampled):
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def y_bins(self) -> NDArray[numpy.float64]:
        """y_bins(self: parselmouth.SampledXY) -> NDArray[numpy.float64]"""
    def y_grid(self) -> NDArray[numpy.float64]:
        """y_grid(self: parselmouth.SampledXY) -> NDArray[numpy.float64]"""
    def ys(self) -> NDArray[numpy.float64]:
        """ys(self: parselmouth.SampledXY) -> NDArray[numpy.float64]"""
    @property
    def dy(self) -> float:
        """(self: parselmouth.SampledXY) -> float"""
    @property
    def ny(self) -> int:
        """(self: parselmouth.SampledXY) -> int"""
    @property
    def y1(self) -> float:
        """(self: parselmouth.SampledXY) -> float"""
    @property
    def ymax(self) -> float:
        """(self: parselmouth.SampledXY) -> float"""
    @property
    def ymin(self) -> float:
        """(self: parselmouth.SampledXY) -> float"""
    @property
    def yrange(self) -> tuple[float, float]:
        """(arg0: parselmouth.SampledXY) -> Tuple[float, float]"""

class SignalOutsideTimeDomain:
    __members__: ClassVar[dict] = ...  # read-only
    SIMILAR: ClassVar[SignalOutsideTimeDomain] = ...
    ZERO: ClassVar[SignalOutsideTimeDomain] = ...
    __entries: ClassVar[dict] = ...
    def __init__(self, *args, **kwargs) -> None:
        """__init__(self: parselmouth.SignalOutsideTimeDomain, value: int) -> None \\\n        __init__(self: parselmouth.SignalOutsideTimeDomain, arg0: str) -> None
        """
    def __eq__(self, other: object) -> bool:
        """__eq__(self: object, other: object) -> bool"""
    def __hash__(self) -> int:
        """__hash__(self: object) -> int"""
    def __index__(self) -> int:
        """__index__(self: parselmouth.SignalOutsideTimeDomain) -> int"""
    def __int__(self) -> int:
        """__int__(self: parselmouth.SignalOutsideTimeDomain) -> int"""
    def __ne__(self, other: object) -> bool:
        """__ne__(self: object, other: object) -> bool"""
    @property
    def name(self) -> str:
        """name(self: handle) -> str

        name(self: handle) -> str
        """
    @property
    def value(self) -> int:
        """(arg0: parselmouth.SignalOutsideTimeDomain) -> int"""

class Sound(TimeFrameSampled, Vector):
    class ToHarmonicityMethod:
        __members__: ClassVar[dict] = ...  # read-only
        AC: ClassVar[Sound.ToHarmonicityMethod] = ...
        CC: ClassVar[Sound.ToHarmonicityMethod] = ...
        GNE: ClassVar[Sound.ToHarmonicityMethod] = ...
        __entries: ClassVar[dict] = ...
        def __init__(self, *args, **kwargs) -> None:
            """__init__(self: parselmouth.Sound.ToHarmonicityMethod, value: int) -> None \\\n            __init__(self: parselmouth.Sound.ToHarmonicityMethod, arg0: str) -> None
            """
        def __eq__(self, other: object) -> bool:
            """__eq__(self: object, other: object) -> bool"""
        def __hash__(self) -> int:
            """__hash__(self: object) -> int"""
        def __index__(self) -> int:
            """__index__(self: parselmouth.Sound.ToHarmonicityMethod) -> int"""
        def __int__(self) -> int:
            """__int__(self: parselmouth.Sound.ToHarmonicityMethod) -> int"""
        def __ne__(self, other: object) -> bool:
            """__ne__(self: object, other: object) -> bool"""
        @property
        def name(self) -> str:
            """name(self: handle) -> str

            name(self: handle) -> str
            """
        @property
        def value(self) -> int:
            """(arg0: parselmouth.Sound.ToHarmonicityMethod) -> int"""

    class ToPitchMethod:
        __members__: ClassVar[dict] = ...  # read-only
        AC: ClassVar[Sound.ToPitchMethod] = ...
        CC: ClassVar[Sound.ToPitchMethod] = ...
        SHS: ClassVar[Sound.ToPitchMethod] = ...
        SPINET: ClassVar[Sound.ToPitchMethod] = ...
        __entries: ClassVar[dict] = ...
        def __init__(self, *args, **kwargs) -> None:
            """__init__(self: parselmouth.Sound.ToPitchMethod, value: int) -> None \\\n            __init__(self: parselmouth.Sound.ToPitchMethod, arg0: str) -> None
            """
        def __eq__(self, other: object) -> bool:
            """__eq__(self: object, other: object) -> bool"""
        def __hash__(self) -> int:
            """__hash__(self: object) -> int"""
        def __index__(self) -> int:
            """__index__(self: parselmouth.Sound.ToPitchMethod) -> int"""
        def __int__(self) -> int:
            """__int__(self: parselmouth.Sound.ToPitchMethod) -> int"""
        def __ne__(self, other: object) -> bool:
            """__ne__(self: object, other: object) -> bool"""
        @property
        def name(self) -> str:
            """name(self: handle) -> str

            name(self: handle) -> str
            """
        @property
        def value(self) -> int:
            """(arg0: parselmouth.Sound.ToPitchMethod) -> int"""
    sampling_frequency: float
    sampling_period: float
    def __init__(self, *args, **kwargs) -> None:
        """__init__(self: parselmouth.Sound, other: parselmouth.Sound) -> None \\\n        __init__(self: parselmouth.Sound, values: NDArray[numpy.float64], sampling_frequency: Positive[float] = 44100.0, start_time: float = 0.0) -> None \\\n        __init__(self: parselmouth.Sound, file_path: str) -> None
        """
    def autocorrelate(self, scaling: AmplitudeScaling = ..., signal_outside_time_domain: SignalOutsideTimeDomain = ...) -> Sound:
        """autocorrelate(self: parselmouth.Sound, scaling: parselmouth.AmplitudeScaling = <AmplitudeScaling.PEAK_0_99: 4>, signal_outside_time_domain: parselmouth.SignalOutsideTimeDomain = <SignalOutsideTimeDomain.ZERO: 1>) -> parselmouth.Sound"""
    @staticmethod
    def combine_to_stereo(sounds: list[Sound]) -> Sound:
        """combine_to_stereo(sounds: List[parselmouth.Sound]) -> parselmouth.Sound"""
    @staticmethod
    def concatenate(sounds: list[Sound], overlap: NonNegative[float] = ...) -> Sound:
        """concatenate(sounds: List[parselmouth.Sound], overlap: NonNegative[float] = 0.0) -> parselmouth.Sound"""
    def convert_to_mono(self) -> Sound:
        """convert_to_mono(self: parselmouth.Sound) -> parselmouth.Sound"""
    def convert_to_stereo(self) -> Sound:
        """convert_to_stereo(self: parselmouth.Sound) -> parselmouth.Sound"""
    def convolve(self, other: Sound, scaling: AmplitudeScaling = ..., signal_outside_time_domain: SignalOutsideTimeDomain = ...) -> Sound:
        """convolve(self: parselmouth.Sound, other: parselmouth.Sound, scaling: parselmouth.AmplitudeScaling = <AmplitudeScaling.PEAK_0_99: 4>, signal_outside_time_domain: parselmouth.SignalOutsideTimeDomain = <SignalOutsideTimeDomain.ZERO: 1>) -> parselmouth.Sound"""
    def cross_correlate(self, other: Sound, scaling: AmplitudeScaling = ..., signal_outside_time_domain: SignalOutsideTimeDomain = ...) -> Sound:
        """cross_correlate(self: parselmouth.Sound, other: parselmouth.Sound, scaling: parselmouth.AmplitudeScaling = <AmplitudeScaling.PEAK_0_99: 4>, signal_outside_time_domain: parselmouth.SignalOutsideTimeDomain = <SignalOutsideTimeDomain.ZERO: 1>) -> parselmouth.Sound"""
    def de_emphasize(self, from_frequency: float = ..., normalize: bool = ...) -> None:
        """de_emphasize(self: parselmouth.Sound, from_frequency: float = 50.0, normalize: bool = True) -> None"""
    def deepen_band_modulation(self, enhancement: Positive[float] = ..., from_frequency: Positive[float] = ..., to_frequency: Positive[float] = ..., slow_modulation: Positive[float] = ..., fast_modulation: Positive[float] = ..., band_smoothing: Positive[float] = ...) -> Sound:
        """deepen_band_modulation(self: parselmouth.Sound, enhancement: Positive[float] = 20.0, from_frequency: Positive[float] = 300.0, to_frequency: Positive[float] = 8000.0, slow_modulation: Positive[float] = 3.0, fast_modulation: Positive[float] = 30.0, band_smoothing: Positive[float] = 100.0) -> parselmouth.Sound"""
    def extract_all_channels(self) -> list[Sound]:
        """extract_all_channels(self: parselmouth.Sound) -> List[parselmouth.Sound]"""
    def extract_channel(self, *args, **kwargs):
        """extract_channel(self: parselmouth.Sound, channel: int) -> parselmouth.Sound \\\n        extract_channel(self: parselmouth.Sound, arg0: str) -> parselmouth.Sound
        """
    def extract_left_channel(self) -> Sound:
        """extract_left_channel(self: parselmouth.Sound) -> parselmouth.Sound"""
    def extract_part(self, from_time: float | None = ..., to_time: float | None = ..., window_shape: WindowShape = ..., relative_width: Positive[float] = ..., preserve_times: bool = ...) -> Sound:
        """extract_part(self: parselmouth.Sound, from_time: Optional[float] = None, to_time: Optional[float] = None, window_shape: parselmouth.WindowShape = <WindowShape.RECTANGULAR: 0>, relative_width: Positive[float] = 1.0, preserve_times: bool = False) -> parselmouth.Sound"""
    def extract_part_for_overlap(self, from_time: float | None = ..., to_time: float | None = ..., overlap: Positive[float] = ...) -> Sound:
        """extract_part_for_overlap(self: parselmouth.Sound, from_time: Optional[float] = None, to_time: Optional[float] = None, overlap: Positive[float]) -> parselmouth.Sound"""
    def extract_right_channel(self) -> Sound:
        """extract_right_channel(self: parselmouth.Sound) -> parselmouth.Sound"""
    def get_energy(self, from_time: float | None = ..., to_time: float | None = ...) -> float:
        """get_energy(self: parselmouth.Sound, from_time: Optional[float] = None, to_time: Optional[float] = None) -> float"""
    def get_energy_in_air(self) -> float:
        """get_energy_in_air(self: parselmouth.Sound) -> float"""
    def get_index_from_time(self, time: float) -> float:
        """get_index_from_time(self: parselmouth.Sound, time: float) -> float"""
    def get_intensity(self) -> float:
        """get_intensity(self: parselmouth.Sound) -> float"""
    def get_nearest_zero_crossing(self, time: float, channel: int = ...) -> float:
        """get_nearest_zero_crossing(self: parselmouth.Sound, time: float, channel: int = 1) -> float"""
    def get_number_of_channels(self) -> int:
        """get_number_of_channels(self: parselmouth.Sound) -> int"""
    def get_number_of_samples(self) -> int:
        """get_number_of_samples(self: parselmouth.Sound) -> int"""
    def get_power(self, from_time: float | None = ..., to_time: float | None = ...) -> float:
        """get_power(self: parselmouth.Sound, from_time: Optional[float] = None, to_time: Optional[float] = None) -> float"""
    def get_power_in_air(self) -> float:
        """get_power_in_air(self: parselmouth.Sound) -> float"""
    def get_rms(self, from_time: float | None = ..., to_time: float | None = ...) -> float:
        """get_rms(self: parselmouth.Sound, from_time: Optional[float] = None, to_time: Optional[float] = None) -> float"""
    def get_root_mean_square(self, from_time: float | None = ..., to_time: float | None = ...) -> float:
        """get_root_mean_square(self: parselmouth.Sound, from_time: Optional[float] = None, to_time: Optional[float] = None) -> float"""
    def get_sampling_frequency(self) -> float:
        """get_sampling_frequency(self: parselmouth.Sound) -> float"""
    def get_sampling_period(self) -> float:
        """get_sampling_period(self: parselmouth.Sound) -> float"""
    def get_time_from_index(self, sample: int) -> float:
        """get_time_from_index(self: parselmouth.Sound, sample: int) -> float"""
    def lengthen(self, minimum_pitch: Positive[float] = ..., maximum_pitch: Positive[float] = ..., factor: Positive[float] = ...) -> Sound:
        """lengthen(self: parselmouth.Sound, minimum_pitch: Positive[float] = 75.0, maximum_pitch: Positive[float] = 600.0, factor: Positive[float]) -> parselmouth.Sound"""
    def multiply_by_window(self, window_shape: WindowShape) -> None:
        """multiply_by_window(self: parselmouth.Sound, window_shape: parselmouth.WindowShape) -> None"""
    def override_sampling_frequency(self, new_frequency: Positive[float]) -> None:
        """override_sampling_frequency(self: parselmouth.Sound, new_frequency: Positive[float]) -> None"""
    def pre_emphasize(self, from_frequency: float = ..., normalize: bool = ...) -> None:
        """pre_emphasize(self: parselmouth.Sound, from_frequency: float = 50.0, normalize: bool = True) -> None"""
    def resample(self, new_frequency: float, precision: int = ...) -> Sound:
        """resample(self: parselmouth.Sound, new_frequency: float, precision: int = 50) -> parselmouth.Sound"""
    def reverse(self, from_time: float | None = ..., to_time: float | None = ...) -> None:
        """reverse(self: parselmouth.Sound, from_time: Optional[float] = None, to_time: Optional[float] = None) -> None"""
    def save(self, file_path: str, format: SoundFileFormat) -> None:  # type: ignore[override]
        """save(self: parselmouth.Sound, file_path: str, format: parselmouth.SoundFileFormat) -> None"""
    def scale_intensity(self, new_average_intensity: float) -> None:
        """scale_intensity(self: parselmouth.Sound, new_average_intensity: float) -> None"""
    def set_to_zero(self, from_time: float | None = ..., to_time: float | None = ..., round_to_nearest_zero_crossing: bool = ...) -> None:
        """set_to_zero(self: parselmouth.Sound, from_time: Optional[float] = None, to_time: Optional[float] = None, round_to_nearest_zero_crossing: bool = True) -> None"""
    def to_formant_burg(self, time_step: Positive[float] | None = ..., max_number_of_formants: Positive[float] = ..., maximum_formant: float = ..., window_length: Positive[float] = ..., pre_emphasis_from: Positive[float] = ...) -> Formant:
        """to_formant_burg(self: parselmouth.Sound, time_step: Optional[Positive[float]] = None, max_number_of_formants: Positive[float] = 5.0, maximum_formant: float = 5500.0, window_length: Positive[float] = 0.025, pre_emphasis_from: Positive[float] = 50.0) -> parselmouth.Formant"""
    def to_harmonicity(self, method: Sound.ToHarmonicityMethod = ..., *args, **kwargs) -> Harmonicity:
        """to_harmonicity(self: parselmouth.Sound, method: parselmouth.Sound.ToHarmonicityMethod = <ToHarmonicityMethod.CC: 0>, *args, **kwargs) -> object"""
    def to_harmonicity_ac(self, time_step: Positive[float] = ..., minimum_pitch: Positive[float] = ..., silence_threshold: float = ..., periods_per_window: Positive[float] = ...) -> Harmonicity:
        """to_harmonicity_ac(self: parselmouth.Sound, time_step: Positive[float] = 0.01, minimum_pitch: Positive[float] = 75.0, silence_threshold: float = 0.1, periods_per_window: Positive[float] = 1.0) -> parselmouth.Harmonicity"""
    def to_harmonicity_cc(self, time_step: Positive[float] = ..., minimum_pitch: Positive[float] = ..., silence_threshold: float = ..., periods_per_window: Positive[float] = ...) -> Harmonicity:
        """to_harmonicity_cc(self: parselmouth.Sound, time_step: Positive[float] = 0.01, minimum_pitch: Positive[float] = 75.0, silence_threshold: float = 0.1, periods_per_window: Positive[float] = 1.0) -> parselmouth.Harmonicity"""
    def to_harmonicity_gne(self, minimum_frequency: Positive[float] = ..., maximum_frequency: Positive[float] = ..., bandwidth: Positive[float] = ..., step: Positive[float] = ...) -> Matrix:
        """to_harmonicity_gne(self: parselmouth.Sound, minimum_frequency: Positive[float] = 500.0, maximum_frequency: Positive[float] = 4500.0, bandwidth: Positive[float] = 1000.0, step: Positive[float] = 80.0) -> parselmouth.Matrix"""
    def to_intensity(self, minimum_pitch: Positive[float] = ..., time_step: Positive[float] | None = ..., subtract_mean: bool = ...) -> Intensity:
        """to_intensity(self: parselmouth.Sound, minimum_pitch: Positive[float] = 100.0, time_step: Optional[Positive[float]] = None, subtract_mean: bool = True) -> parselmouth.Intensity"""
    def to_mfcc(self, number_of_coefficients: Positive[int] = ..., window_length: Positive[float] = ..., time_step: Positive[float] = ..., firstFilterFreqency: Positive[float] = ..., distance_between_filters: Positive[float] = ..., maximum_frequency: Positive[float] | None = ...) -> MFCC:
        """to_mfcc(self: parselmouth.Sound, number_of_coefficients: Positive[int] = 12, window_length: Positive[float] = 0.015, time_step: Positive[float] = 0.005, firstFilterFreqency: Positive[float] = 100.0, distance_between_filters: Positive[float] = 100.0, maximum_frequency: Optional[Positive[float]] = None) -> parselmouth.MFCC"""
    def to_pitch(self, *args, **kwargs):
        """to_pitch(self: parselmouth.Sound, time_step: Optional[Positive[float]] = None, pitch_floor: Positive[float] = 75.0, pitch_ceiling: Positive[float] = 600.0) -> parselmouth.Pitch \\\n        to_pitch(self: parselmouth.Sound, method: parselmouth.Sound.ToPitchMethod, *args, **kwargs) -> object
        """
    def to_pitch_ac(self, time_step: Positive[float] | None = ..., pitch_floor: Positive[float] = ..., max_number_of_candidates: Positive[int] = ..., very_accurate: bool = ..., silence_threshold: float = ..., voicing_threshold: float = ..., octave_cost: float = ..., octave_jump_cost: float = ..., voiced_unvoiced_cost: float = ..., pitch_ceiling: Positive[float] = ...) -> Pitch:
        """to_pitch_ac(self: parselmouth.Sound, time_step: Optional[Positive[float]] = None, pitch_floor: Positive[float] = 75.0, max_number_of_candidates: Positive[int] = 15, very_accurate: bool = False, silence_threshold: float = 0.03, voicing_threshold: float = 0.45, octave_cost: float = 0.01, octave_jump_cost: float = 0.35, voiced_unvoiced_cost: float = 0.14, pitch_ceiling: Positive[float] = 600.0) -> parselmouth.Pitch"""
    def to_pitch_cc(self, time_step: Positive[float] | None = ..., pitch_floor: Positive[float] = ..., max_number_of_candidates: Positive[int] = ..., very_accurate: bool = ..., silence_threshold: float = ..., voicing_threshold: float = ..., octave_cost: float = ..., octave_jump_cost: float = ..., voiced_unvoiced_cost: float = ..., pitch_ceiling: Positive[float] = ...) -> Pitch:
        """to_pitch_cc(self: parselmouth.Sound, time_step: Optional[Positive[float]] = None, pitch_floor: Positive[float] = 75.0, max_number_of_candidates: Positive[int] = 15, very_accurate: bool = False, silence_threshold: float = 0.03, voicing_threshold: float = 0.45, octave_cost: float = 0.01, octave_jump_cost: float = 0.35, voiced_unvoiced_cost: float = 0.14, pitch_ceiling: Positive[float] = 600.0) -> parselmouth.Pitch"""
    def to_pitch_shs(self, time_step: Positive[float] = ..., minimum_pitch: Positive[float] = ..., max_number_of_candidates: Positive[int] = ..., maximum_frequency_component: Positive[float] = ..., max_number_of_subharmonics: Positive[int] = ..., compression_factor: Positive[float] = ..., ceiling: Positive[float] = ..., number_of_points_per_octave: Positive[int] = ...) -> Pitch:
        """to_pitch_shs(self: parselmouth.Sound, time_step: Positive[float] = 0.01, minimum_pitch: Positive[float] = 50.0, max_number_of_candidates: Positive[int] = 15, maximum_frequency_component: Positive[float] = 1250.0, max_number_of_subharmonics: Positive[int] = 15, compression_factor: Positive[float] = 0.84, ceiling: Positive[float] = 600.0, number_of_points_per_octave: Positive[int] = 48) -> parselmouth.Pitch"""
    def to_pitch_spinet(self, time_step: Positive[float] = ..., window_length: Positive[float] = ..., minimum_filter_frequency: Positive[float] = ..., maximum_filter_frequency: Positive[float] = ..., number_of_filters: Positive[int] = ..., ceiling: Positive[float] = ..., max_number_of_candidates: Positive[int] = ...) -> Pitch:
        """to_pitch_spinet(self: parselmouth.Sound, time_step: Positive[float] = 0.005, window_length: Positive[float] = 0.04, minimum_filter_frequency: Positive[float] = 70.0, maximum_filter_frequency: Positive[float] = 5000.0, number_of_filters: Positive[int] = 250, ceiling: Positive[float] = 500.0, max_number_of_candidates: Positive[int] = 15) -> parselmouth.Pitch"""
    def to_spectrogram(self, window_length: Positive[float] = ..., maximum_frequency: Positive[float] = ..., time_step: Positive[float] = ..., frequency_step: Positive[float] = ..., window_shape: SpectralAnalysisWindowShape = ...) -> Spectrogram:
        """to_spectrogram(self: parselmouth.Sound, window_length: Positive[float] = 0.005, maximum_frequency: Positive[float] = 5000.0, time_step: Positive[float] = 0.002, frequency_step: Positive[float] = 20.0, window_shape: parselmouth.SpectralAnalysisWindowShape = <SpectralAnalysisWindowShape.GAUSSIAN: 5>) -> parselmouth.Spectrogram"""
    def to_spectrum(self, fast: bool = ...) -> Spectrum:
        """to_spectrum(self: parselmouth.Sound, fast: bool = True) -> parselmouth.Spectrum"""
    @property
    def n_channels(self) -> int:
        """(self: parselmouth.Sound) -> int"""
    @property
    def n_samples(self) -> int:
        """(self: parselmouth.Sound) -> int"""

class SoundFileFormat:
    __members__: ClassVar[dict] = ...  # read-only
    AIFC: ClassVar[SoundFileFormat] = ...
    AIFF: ClassVar[SoundFileFormat] = ...
    FLAC: ClassVar[SoundFileFormat] = ...
    KAY: ClassVar[SoundFileFormat] = ...
    NEXT_SUN: ClassVar[SoundFileFormat] = ...
    NIST: ClassVar[SoundFileFormat] = ...
    RAW_16_BE: ClassVar[SoundFileFormat] = ...
    RAW_16_LE: ClassVar[SoundFileFormat] = ...
    RAW_24_BE: ClassVar[SoundFileFormat] = ...
    RAW_24_LE: ClassVar[SoundFileFormat] = ...
    RAW_32_BE: ClassVar[SoundFileFormat] = ...
    RAW_32_LE: ClassVar[SoundFileFormat] = ...
    RAW_8_SIGNED: ClassVar[SoundFileFormat] = ...
    RAW_8_UNSIGNED: ClassVar[SoundFileFormat] = ...
    SESAM: ClassVar[SoundFileFormat] = ...
    WAV: ClassVar[SoundFileFormat] = ...
    WAV_24: ClassVar[SoundFileFormat] = ...
    WAV_32: ClassVar[SoundFileFormat] = ...
    __entries: ClassVar[dict] = ...
    def __init__(self, *args, **kwargs) -> None:
        """__init__(self: parselmouth.SoundFileFormat, value: int) -> None \\\n        __init__(self: parselmouth.SoundFileFormat, arg0: str) -> None
        """
    def __eq__(self, other: object) -> bool:
        """__eq__(self: object, other: object) -> bool"""
    def __hash__(self) -> int:
        """__hash__(self: object) -> int"""
    def __index__(self) -> int:
        """__index__(self: parselmouth.SoundFileFormat) -> int"""
    def __int__(self) -> int:
        """__int__(self: parselmouth.SoundFileFormat) -> int"""
    def __ne__(self, other: object) -> bool:
        """__ne__(self: object, other: object) -> bool"""
    @property
    def name(self) -> str:
        """name(self: handle) -> str

        name(self: handle) -> str
        """
    @property
    def value(self) -> int:
        """(arg0: parselmouth.SoundFileFormat) -> int"""

class SpectralAnalysisWindowShape:
    __members__: ClassVar[dict] = ...  # read-only
    BARTLETT: ClassVar[SpectralAnalysisWindowShape] = ...
    GAUSSIAN: ClassVar[SpectralAnalysisWindowShape] = ...
    HAMMING: ClassVar[SpectralAnalysisWindowShape] = ...
    HANNING: ClassVar[SpectralAnalysisWindowShape] = ...
    SQUARE: ClassVar[SpectralAnalysisWindowShape] = ...
    WELCH: ClassVar[SpectralAnalysisWindowShape] = ...
    __entries: ClassVar[dict] = ...
    def __init__(self, *args, **kwargs) -> None:
        """__init__(self: parselmouth.SpectralAnalysisWindowShape, value: int) -> None \\\n        __init__(self: parselmouth.SpectralAnalysisWindowShape, arg0: str) -> None
        """
    def __eq__(self, other: object) -> bool:
        """__eq__(self: object, other: object) -> bool"""
    def __hash__(self) -> int:
        """__hash__(self: object) -> int"""
    def __index__(self) -> int:
        """__index__(self: parselmouth.SpectralAnalysisWindowShape) -> int"""
    def __int__(self) -> int:
        """__int__(self: parselmouth.SpectralAnalysisWindowShape) -> int"""
    def __ne__(self, other: object) -> bool:
        """__ne__(self: object, other: object) -> bool"""
    @property
    def name(self) -> str:
        """name(self: handle) -> str

        name(self: handle) -> str
        """
    @property
    def value(self) -> int:
        """(arg0: parselmouth.SpectralAnalysisWindowShape) -> int"""

class Spectrogram(TimeFrameSampled, Matrix):
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def get_power_at(self, time: float, frequency: float) -> float:
        """get_power_at(self: parselmouth.Spectrogram, time: float, frequency: float) -> float"""
    def synthesize_sound(self, sampling_frequency: Positive[float] = ...) -> Sound:
        """synthesize_sound(self: parselmouth.Spectrogram, sampling_frequency: Positive[float] = 44100.0) -> parselmouth.Sound"""
    def to_sound(self, sampling_frequency: Positive[float] = ...) -> Sound:
        """to_sound(self: parselmouth.Spectrogram, sampling_frequency: Positive[float] = 44100.0) -> parselmouth.Sound"""
    def to_spectrum_slice(self, time: float) -> Spectrum:
        """to_spectrum_slice(self: parselmouth.Spectrogram, time: float) -> parselmouth.Spectrum"""

class Spectrum(Matrix):
    def __init__(self, *args, **kwargs) -> None:
        """__init__(self: parselmouth.Spectrum, values: NDArray[numpy.float64], maximum_frequency: Positive[float]) -> None \\\n        __init__(self: parselmouth.Spectrum, values: numpy.ndarray[numpy.complex128], maximum_frequency: Positive[float]) -> None
        """
    def cepstral_smoothing(self, bandwidth: Positive[float] = ...) -> Spectrum:
        """cepstral_smoothing(self: parselmouth.Spectrum, bandwidth: Positive[float] = 500.0) -> parselmouth.Spectrum"""
    def get_band_density(self, *args, **kwargs):
        """get_band_density(self: parselmouth.Spectrum, band_floor: Optional[float] = None, band_ceiling: Optional[float] = None) -> float \\\n        get_band_density(self: parselmouth.Spectrum, band: Tuple[Optional[float], Optional[float]] = (None, None)) -> float
        """
    def get_band_density_difference(self, *args, **kwargs):
        """get_band_density_difference(self: parselmouth.Spectrum, low_band_floor: Optional[float] = None, low_band_ceiling: Optional[float] = None, high_band_floor: Optional[float] = None, high_band_ceiling: Optional[float] = None) -> float \\\n        get_band_density_difference(self: parselmouth.Spectrum, low_band: Tuple[Optional[float], Optional[float]] = (None, None), high_band: Tuple[Optional[float], Optional[float]] = (None, None)) -> float
        """
    def get_band_energy(self, *args, **kwargs):
        """get_band_energy(self: parselmouth.Spectrum, band_floor: Optional[float] = None, band_ceiling: Optional[float] = None) -> float \\\n        get_band_energy(self: parselmouth.Spectrum, band: Tuple[Optional[float], Optional[float]] = (None, None)) -> float
        """
    def get_band_energy_difference(self, *args, **kwargs):
        """get_band_energy_difference(self: parselmouth.Spectrum, low_band_floor: Optional[float] = None, low_band_ceiling: Optional[float] = None, high_band_floor: Optional[float] = None, high_band_ceiling: Optional[float] = None) -> float \\\n        get_band_energy_difference(self: parselmouth.Spectrum, low_band: Tuple[Optional[float], Optional[float]] = (None, None), high_band: Tuple[Optional[float], Optional[float]] = (None, None)) -> float
        """
    def get_bin_number_from_frequency(self, frequency: float) -> float:
        """get_bin_number_from_frequency(self: parselmouth.Spectrum, frequency: float) -> float"""
    def get_bin_width(self) -> float:
        """get_bin_width(self: parselmouth.Spectrum) -> float"""
    def get_center_of_gravity(self, power: Positive[float] = ...) -> float:
        """get_center_of_gravity(self: parselmouth.Spectrum, power: Positive[float] = 2.0) -> float"""
    def get_central_moment(self, moment: Positive[float], power: Positive[float] = ...) -> float:
        """get_central_moment(self: parselmouth.Spectrum, moment: Positive[float], power: Positive[float] = 2.0) -> float"""
    def get_centre_of_gravity(self, power: Positive[float] = ...) -> float:
        """get_centre_of_gravity(self: parselmouth.Spectrum, power: Positive[float] = 2.0) -> float"""
    def get_frequency_from_bin_number(self, band_number: Positive[int]) -> float:
        """get_frequency_from_bin_number(self: parselmouth.Spectrum, band_number: Positive[int]) -> float"""
    def get_highest_frequency(self) -> float:
        """get_highest_frequency(self: parselmouth.Spectrum) -> float"""
    def get_imaginary_value_in_bin(self, bin_number: Positive[int]) -> float:
        """get_imaginary_value_in_bin(self: parselmouth.Spectrum, bin_number: Positive[int]) -> float"""
    def get_kurtosis(self, power: Positive[float] = ...) -> float:
        """get_kurtosis(self: parselmouth.Spectrum, power: Positive[float] = 2.0) -> float"""
    def get_lowest_frequency(self) -> float:
        """get_lowest_frequency(self: parselmouth.Spectrum) -> float"""
    def get_number_of_bins(self) -> int:
        """get_number_of_bins(self: parselmouth.Spectrum) -> int"""
    def get_real_value_in_bin(self, bin_number: Positive[int]) -> float:
        """get_real_value_in_bin(self: parselmouth.Spectrum, bin_number: Positive[int]) -> float"""
    def get_skewness(self, power: Positive[float] = ...) -> float:
        """get_skewness(self: parselmouth.Spectrum, power: Positive[float] = 2.0) -> float"""
    def get_standard_deviation(self, power: Positive[float] = ...) -> float:
        """get_standard_deviation(self: parselmouth.Spectrum, power: Positive[float] = 2.0) -> float"""
    def get_value_in_bin(self, bin_number: Positive[int]) -> complex:
        """get_value_in_bin(self: parselmouth.Spectrum, bin_number: Positive[int]) -> complex"""
    def lpc_smoothing(self, num_peaks: Positive[int] = ..., pre_emphasis_from: Positive[float] = ...) -> Spectrum:
        """lpc_smoothing(self: parselmouth.Spectrum, num_peaks: Positive[int] = 5, pre_emphasis_from: Positive[float] = 50.0) -> parselmouth.Spectrum"""
    def set_imaginary_value_in_bin(self, bin_number: Positive[int], value: float) -> None:
        """set_imaginary_value_in_bin(self: parselmouth.Spectrum, bin_number: Positive[int], value: float) -> None"""
    def set_real_value_in_bin(self, bin_number: Positive[int], value: float) -> None:
        """set_real_value_in_bin(self: parselmouth.Spectrum, bin_number: Positive[int], value: float) -> None"""
    def set_value_in_bin(self, bin_number: Positive[int], value: complex) -> None:
        """set_value_in_bin(self: parselmouth.Spectrum, bin_number: Positive[int], value: complex) -> None"""
    def to_sound(self) -> Sound:
        """to_sound(self: parselmouth.Spectrum) -> parselmouth.Sound"""
    def to_spectrogram(self) -> Spectrogram:
        """to_spectrogram(self: parselmouth.Spectrum) -> parselmouth.Spectrogram"""
    def __getitem__(self, index: int) -> complex:
        """__getitem__(self: parselmouth.Spectrum, index: int) -> complex"""
    def __iter__(self) -> typing.Iterator[complex]:
        """def __iter__(self) -> typing.Iterator[complex]"""
    def __setitem__(self, index: int, value: complex) -> None:
        """__setitem__(self: parselmouth.Spectrum, index: int, value: complex) -> None"""
    @property
    def bin_width(self) -> float:
        """(self: parselmouth.Spectrum) -> float"""
    @property
    def df(self) -> float:
        """(self: parselmouth.Spectrum) -> float"""
    @property
    def fmax(self) -> float:
        """(self: parselmouth.Spectrum) -> float"""
    @property
    def fmin(self) -> float:
        """(self: parselmouth.Spectrum) -> float"""
    @property
    def highest_frequency(self) -> float:
        """(self: parselmouth.Spectrum) -> float"""
    @property
    def lowest_frequency(self) -> float:
        """(self: parselmouth.Spectrum) -> float"""
    @property
    def n_bins(self) -> int:
        """(self: parselmouth.Spectrum) -> int"""
    @property
    def nf(self) -> int:
        """(self: parselmouth.Spectrum) -> int"""

class TextGrid(Function):
    def __init__(self, *args, **kwargs) -> None:
        """__init__(self: parselmouth.TextGrid, start_time: float, end_time: float, tier_names: str, point_tier_names: str) -> None \\\n        __init__(self: parselmouth.TextGrid, start_time: float, end_time: float, tier_names: List[str] = [], point_tier_names: List[str] = []) -> None \\\n        __init__(self: parselmouth.TextGrid, tgt_text_grid: tgt.core.TextGrid) -> None
        """
    @staticmethod
    def from_tgt(tgt_text_grid: tgt.core.TextGrid) -> TextGrid:
        """from_tgt(tgt_text_grid: tgt.core.TextGrid) -> parselmouth.TextGrid"""
    def to_tgt(self, include_empty_intervals: bool = ...) -> tgt.core.TextGrid:
        """to_tgt(self: parselmouth.TextGrid, *, include_empty_intervals: bool = False) -> tgt.core.TextGrid"""

class Thing:
    name: str
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def info(self) -> str:
        """info(self: parselmouth.Thing) -> str"""
    @property
    def class_name(self) -> str:
        """(arg0: parselmouth.Thing) -> str"""
    @property
    def full_name(self) -> str:
        """(arg0: parselmouth.Thing) -> str"""

class TimeFrameSampled(TimeFunction, Sampled):
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def frame_number_to_time(self, frame_number: Positive[int]) -> float:
        """frame_number_to_time(self: parselmouth.Sampled, frame_number: Positive[int]) -> float"""
    def get_frame_number_from_time(self, time: float) -> float:
        """get_frame_number_from_time(self: parselmouth.Sampled, time: float) -> float"""
    def get_number_of_frames(self) -> int:
        """get_number_of_frames(self: parselmouth.Sampled) -> int"""
    def get_time_from_frame_number(self, frame_number: Positive[int]) -> float:
        """get_time_from_frame_number(self: parselmouth.Sampled, frame_number: Positive[int]) -> float"""
    def get_time_step(self) -> float:
        """get_time_step(self: parselmouth.Sampled) -> float"""
    def t_bins(self) -> NDArray[numpy.float64]:
        """t_bins(self: parselmouth.Sampled) -> NDArray[numpy.float64]"""
    def t_grid(self) -> NDArray[numpy.float64]:
        """t_grid(self: parselmouth.Sampled) -> NDArray[numpy.float64]"""
    def time_to_frame_number(self, time: float) -> float:
        """time_to_frame_number(self: parselmouth.Sampled, time: float) -> float"""
    def ts(self) -> NDArray[numpy.float64]:
        """ts(self: parselmouth.Sampled) -> NDArray[numpy.float64]"""
    @property
    def dt(self) -> float:
        """(self: parselmouth.TimeFrameSampled) -> float"""
    @property
    def n_frames(self) -> int:
        """(self: parselmouth.TimeFrameSampled) -> int"""
    @property
    def nt(self) -> int:
        """(self: parselmouth.TimeFrameSampled) -> int"""
    @property
    def t1(self) -> float:
        """(self: parselmouth.TimeFrameSampled) -> float"""
    @property
    def time_step(self) -> float:
        """(self: parselmouth.TimeFrameSampled) -> float"""

class TimeFunction(Function):
    centre_time: float
    end_time: float
    start_time: float
    time_range: tuple[float, float]
    tmax: float
    tmin: float
    trange: tuple[float, float]
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def get_end_time(self) -> float:
        """get_end_time(self: parselmouth.Function) -> float"""
    def get_start_time(self) -> float:
        """get_start_time(self: parselmouth.Function) -> float"""
    def get_total_duration(self) -> float:
        """get_total_duration(self: parselmouth.Function) -> float"""
    def scale_times_by(self, scale: Positive[float]) -> None:
        """scale_times_by(self: parselmouth.Function, scale: Positive[float]) -> None"""
    def scale_times_to(self, new_start_time: float, new_end_time: float) -> None:
        """scale_times_to(self: parselmouth.Function, new_start_time: float, new_end_time: float) -> None"""
    def shift_times_by(self, seconds: float) -> None:
        """shift_times_by(self: parselmouth.Function, seconds: float) -> None"""
    def shift_times_to(self, *args, **kwargs):
        """shift_times_to(self: parselmouth.Function, time: float, new_time: float) -> None \\\n        shift_times_to(self: parselmouth.Function, time: str, new_time: float) -> None
        """
    @property
    def duration(self) -> float:
        """(arg0: parselmouth.Function) -> float"""
    @property
    def total_duration(self) -> float:
        """(arg0: parselmouth.Function) -> float"""

class ValueInterpolation:
    __members__: ClassVar[dict] = ...  # read-only
    CUBIC: ClassVar[ValueInterpolation] = ...
    LINEAR: ClassVar[ValueInterpolation] = ...
    NEAREST: ClassVar[ValueInterpolation] = ...
    SINC70: ClassVar[ValueInterpolation] = ...
    SINC700: ClassVar[ValueInterpolation] = ...
    __entries: ClassVar[dict] = ...
    def __init__(self, *args, **kwargs) -> None:
        """__init__(self: parselmouth.ValueInterpolation, value: int) -> None \\\n        __init__(self: parselmouth.ValueInterpolation, arg0: str) -> None
        """
    def __eq__(self, other: object) -> bool:
        """__eq__(self: object, other: object) -> bool"""
    def __hash__(self) -> int:
        """__hash__(self: object) -> int"""
    def __index__(self) -> int:
        """__index__(self: parselmouth.ValueInterpolation) -> int"""
    def __int__(self) -> int:
        """__int__(self: parselmouth.ValueInterpolation) -> int"""
    def __ne__(self, other: object) -> bool:
        """__ne__(self: object, other: object) -> bool"""
    @property
    def name(self) -> str:
        """name(self: handle) -> str

        name(self: handle) -> str
        """
    @property
    def value(self) -> int:
        """(arg0: parselmouth.ValueInterpolation) -> int"""

class Vector(Matrix):
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def add(self, number: float) -> None:
        """add(self: parselmouth.Vector, number: float) -> None"""
    def divide(self, factor: float) -> None:
        """divide(self: parselmouth.Vector, factor: float) -> None"""
    def get_value(self, x: float, channel: int | None = ..., interpolation: ValueInterpolation = ...) -> float:
        """get_value(self: parselmouth.Vector, x: float, channel: Optional[int] = None, interpolation: parselmouth.ValueInterpolation = <ValueInterpolation.CUBIC: 2>) -> float"""
    def multiply(self, factor: float) -> None:
        """multiply(self: parselmouth.Vector, factor: float) -> None"""
    def scale(self, scale: Positive[float]) -> None:
        """scale(self: parselmouth.Vector, scale: Positive[float]) -> None"""
    def scale_peak(self, new_peak: Positive[float] = ...) -> None:
        """scale_peak(self: parselmouth.Vector, new_peak: Positive[float] = 0.99) -> None"""
    def subtract(self, number: float) -> None:
        """subtract(self: parselmouth.Vector, number: float) -> None"""
    def subtract_mean(self) -> None:
        """subtract_mean(self: parselmouth.Vector) -> None"""
    def __add__(self, number: float) -> Vector:
        """__add__(self: parselmouth.Vector, number: float) -> parselmouth.Vector"""
    def __iadd__(self, number: float) -> Vector:
        """__iadd__(self: parselmouth.Vector, number: float) -> parselmouth.Vector"""
    def __imul__(self, factor: float) -> Vector:
        """__imul__(self: parselmouth.Vector, factor: float) -> parselmouth.Vector"""
    def __isub__(self, number: float) -> Vector:
        """__isub__(self: parselmouth.Vector, number: float) -> parselmouth.Vector"""
    def __itruediv__(self, factor: float) -> Vector:
        """__itruediv__(self: parselmouth.Vector, factor: float) -> parselmouth.Vector"""
    def __mul__(self, factor: float) -> Vector:
        """__mul__(self: parselmouth.Vector, factor: float) -> parselmouth.Vector"""
    def __radd__(self, number: float) -> Vector:
        """__radd__(self: parselmouth.Vector, number: float) -> parselmouth.Vector"""
    def __rmul__(self, factor: float) -> Vector:
        """__rmul__(self: parselmouth.Vector, factor: float) -> parselmouth.Vector"""
    def __sub__(self, number: float) -> Vector:
        """__sub__(self: parselmouth.Vector, number: float) -> parselmouth.Vector"""
    def __truediv__(self, factor: float) -> Vector:
        """__truediv__(self: parselmouth.Vector, factor: float) -> parselmouth.Vector"""

class WindowShape:
    __members__: ClassVar[dict] = ...  # read-only
    GAUSSIAN1: ClassVar[WindowShape] = ...
    GAUSSIAN2: ClassVar[WindowShape] = ...
    GAUSSIAN3: ClassVar[WindowShape] = ...
    GAUSSIAN4: ClassVar[WindowShape] = ...
    GAUSSIAN5: ClassVar[WindowShape] = ...
    HAMMING: ClassVar[WindowShape] = ...
    HANNING: ClassVar[WindowShape] = ...
    KAISER1: ClassVar[WindowShape] = ...
    KAISER2: ClassVar[WindowShape] = ...
    PARABOLIC: ClassVar[WindowShape] = ...
    RECTANGULAR: ClassVar[WindowShape] = ...
    TRIANGULAR: ClassVar[WindowShape] = ...
    __entries: ClassVar[dict] = ...
    def __init__(self, *args, **kwargs) -> None:
        """__init__(self: parselmouth.WindowShape, value: int) -> None \\\n        __init__(self: parselmouth.WindowShape, arg0: str) -> None
        """
    def __eq__(self, other: object) -> bool:
        """__eq__(self: object, other: object) -> bool"""
    def __hash__(self) -> int:
        """__hash__(self: object) -> int"""
    def __index__(self) -> int:
        """__index__(self: parselmouth.WindowShape) -> int"""
    def __int__(self) -> int:
        """__int__(self: parselmouth.WindowShape) -> int"""
    def __ne__(self, other: object) -> bool:
        """__ne__(self: object, other: object) -> bool"""
    @property
    def name(self) -> str:
        """name(self: handle) -> str

        name(self: handle) -> str
        """
    @property
    def value(self) -> int:
        """(arg0: parselmouth.WindowShape) -> int"""

def read(file_path: str) -> Data:
    """read(file_path: str) -> parselmouth.Data

    Read a file into a `parselmouth.Data` object.

    Parameters
    ----------
    file_path : str
        The path of the file on disk to read.

    Returns
    -------
    parselmouth.Data
        The Praat Data object that was read.

    See also
    --------
    :praat:`Read from file...`
    """
