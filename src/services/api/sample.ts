import type { SampleDataType } from "../../types/sample";
import apiClient from "../utils/axios";


export const fetchData = async (): Promise<SampleDataType> => {
  const response = await apiClient.get<SampleDataType>("/data/");
  return response.data;
};