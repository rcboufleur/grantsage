import streamlit as st

from grantsage import APP_TITLE, APP_SUBTITLE, get_version


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon=":money_with_wings:")
    st.title(APP_TITLE)
    st.subheader(APP_SUBTITLE)
    st.write(f"Versão: {get_version()}")


if __name__ == "__main__":
    main()
