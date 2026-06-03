use std::fmt::{Display, Formatter};

#[derive(Debug, Clone, PartialEq)]
pub enum EcoError {
    Shape(String),
    InvalidInput(String),
    Truncation(String),
}

impl Display for EcoError {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            EcoError::Shape(msg) => write!(f, "shape error: {msg}"),
            EcoError::InvalidInput(msg) => write!(f, "invalid input: {msg}"),
            EcoError::Truncation(msg) => write!(f, "truncation error: {msg}"),
        }
    }
}

impl std::error::Error for EcoError {}

pub type Result<T> = std::result::Result<T, EcoError>;
