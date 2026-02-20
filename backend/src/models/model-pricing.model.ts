import mongoose from 'mongoose';

export interface IModelPricing {
  _id: string;
  modelId: string;
  displayName: string;
  inputPricePerMTok: number;
  outputPricePerMTok: number;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

const modelPricingSchema = new mongoose.Schema({
  _id: { type: String, required: true },
  modelId: { type: String, required: true, unique: true },
  displayName: { type: String, required: true },
  inputPricePerMTok: { type: Number, required: true, min: 0 },
  outputPricePerMTok: { type: Number, required: true, min: 0 },
  isActive: { type: Boolean, default: true },
  createdAt: { type: Date, default: Date.now },
  updatedAt: { type: Date, default: Date.now },
});

modelPricingSchema.pre('save', function(next) {
  this.updatedAt = new Date();
  next();
});

export const ModelPricing = mongoose.model<IModelPricing>('ModelPricing', modelPricingSchema, 'model_pricing');

export const DEFAULT_MODEL_PRICING: Omit<IModelPricing, '_id' | 'createdAt' | 'updatedAt'>[] = [
  {
    modelId: 'claude-sonnet-4-5-20250514',
    displayName: 'Claude Sonnet 4.5',
    inputPricePerMTok: 3,
    outputPricePerMTok: 15,
    isActive: true,
  },
  {
    modelId: 'claude-haiku-4-5-20251001',
    displayName: 'Claude Haiku 4.5',
    inputPricePerMTok: 1,
    outputPricePerMTok: 5,
    isActive: true,
  },
  {
    modelId: 'claude-opus-4-5-20251101',
    displayName: 'Claude Opus 4.5',
    inputPricePerMTok: 5.5,
    outputPricePerMTok: 27.5,
    isActive: true,
  },
];
