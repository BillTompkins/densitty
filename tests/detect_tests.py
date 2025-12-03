import sys

from densitty import axis, detect
import gen_norm_data

if __name__ == "__main__":
    combining_support = detect.combining_support(debug=True)
    color_support = detect.color_support(debug=True)
    print(f"Combining support: {combining_support}")
    print(f"Color support: {color_support}")
    print("")
    data = gen_norm_data.gen_norm(num_rows=20, num_cols=20, width=0.3, height=0.15, angle=0.5)
    y_axis = axis.Axis((-1, 1), border_line=False, values_are_edges=True)
    x_axis = axis.Axis((-1, 1), border_line=False, values_are_edges=True)
    plot = detect.plot(data, y_axis=y_axis, x_axis=x_axis, min_data=-0.1)
    plot.show()
    print("")
    print("Getting VT100 code")
    response = detect.get_code_response("\033[c", response_terminator="c")
    print(f"Response {list(response)}")

    print("Getting Term Param")
    try:
        response = detect.get_code_response("\033[x", response_terminator="x")
        print(f"Response {list(response)}")
    except:
        print("No response")

    print("Getting DA1—Primary Device Attributes")
    try:
        response = detect.get_code_response("\033[c", response_terminator="c")
        print(f"Response {list(response)}")
    except:
        print("No response")

    print("Getting DA2—Secondary Device Attributes")
    try:
        response = detect.get_code_response("\033[>c", response_terminator="c")
        print(f"Response {list(response)}")
    except:
        print("No response")

    print("Getting DA3—Tertiary Device Attributes")
    try:
        response = detect.get_code_response("\033[=c", response_terminator="c")
        print(f"Response {list(response)}")
    except:
        print("No response")
